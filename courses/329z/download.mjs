/** Optional fetch transport for hosts where Python HTTP is unavailable.
 * node courses/329z/download.mjs /absolute/staging-directory
 * Saves response bytes plus a provenance log. sync.py --import-downloads validates
 * file contents before publishing them. No response is labelled saved here.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

async function bounded(promise, milliseconds, abort) {
  let timer;
  try {
    return await Promise.race([promise,new Promise((_,reject)=>{
      timer=setTimeout(()=>{abort?.();reject(new Error('Transport timeout'));},milliseconds);
    })]);
  } finally { clearTimeout(timer); }
}

export async function downloadResources(courseRoot, staging, concurrency=4) {
  const manifest=JSON.parse(await fs.readFile(path.join(courseRoot,'manifest.json'),'utf8'));
  const jobs=manifest.resources.filter(r=>r.status!=='saved');
  const logFile=path.join(staging,'download-log.json');
  await fs.mkdir(staging,{recursive:true});
  let log=[];
  try { log=JSON.parse(await fs.readFile(logFile,'utf8')); } catch (e) { if(e.code!=='ENOENT')throw e; }
  const results=[];
  let checkpoint=Promise.resolve();
  let cursor=0;
  async function worker() {
    while(cursor<jobs.length) {
      const job=jobs[cursor++];
      const target=path.resolve(staging,job.path);
      if(!target.startsWith(path.resolve(staging)+path.sep))throw new Error('Unsafe path');
      const row={url:job.url,download_url:job.download_url,path:job.path,attempted_at:new Date().toISOString()};
      try {
        const controller=new AbortController();
        const response=await bounded(fetch(job.download_url,{signal:controller.signal,headers:{'User-Agent':'CS329Z-public-study-archive/1.0'}}),45000,()=>controller.abort());
        row.http_status=response.status;
        row.final_url=response.url;
        row.content_type=response.headers.get('content-type');
        row.content_disposition=response.headers.get('content-disposition');
        if(!response.ok)throw new Error('HTTP '+response.status);
        const data=Buffer.from(await bounded(response.arrayBuffer(),45000,()=>controller.abort()));
        if(!data.length)throw new Error('Empty response');
        await fs.mkdir(path.dirname(target),{recursive:true});
        await fs.writeFile(target,data);
        row.retrieved_at=new Date().toISOString();
        row.sha256=createHash('sha256').update(data).digest('hex');
        row.bytes=data.length;
        row.transport_status='downloaded_unvalidated';
      } catch(e) {
        row.transport_status='failed';
        row.error=String(e).slice(0,500);
      }
      results.push(row);
      // Persist each completed request; a hung later response cannot lose provenance.
      checkpoint=checkpoint.then(async()=>{
        log=log.filter(r=>r.url!==row.url).concat(row);
        await fs.writeFile(logFile,JSON.stringify(log,null,2)+'\n');
      });
      await checkpoint;
    }
  }
  await Promise.all(Array.from({length:concurrency},worker));
  const replacements=new Set(results.map(r=>r.url));
  log=log.filter(r=>!replacements.has(r.url)).concat(results);
  await fs.writeFile(logFile,JSON.stringify(log,null,2)+'\n');
  return results.map(r=>({url:r.url,status:r.transport_status,bytes:r.bytes,error:r.error}));
}

/** Fetch a bounded batch of original byte ranges. Range offsets/ETag/lengths
 * are checked before concatenation; content is never converted or rewritten.
 * A batch returns after at most limit chunks, allowing progress checkpoints.
 */
export async function downloadRangeBatch(url,target,limit=24,concurrency=12,chunkBytes=65536) {
  const parts=target+'.parts';
  await fs.mkdir(parts,{recursive:true});
  const metaFile=path.join(parts,'source.json');
  let meta;
  try { meta=JSON.parse(await fs.readFile(metaFile,'utf8')); } catch(e) { if(e.code!=='ENOENT')throw e; }
  async function fetchChunk(index,known) {
    const start=index*chunkBytes;
    const end=known?Math.min(start+chunkBytes-1,known.total-1):start+chunkBytes-1;
    const controller=new AbortController();
      return await bounded((async()=>{
        const headers={Range:`bytes=${start}-${end}`};
        if(known?.etag)headers['If-Range']=known.etag;
        const response=await fetch(url,{headers,signal:controller.signal});
        const range=/^bytes (\d+)-(\d+)\/(\d+)$/.exec(response.headers.get('content-range')||'');
        if(response.status!==206||!range||Number(range[1])!==start||Number(range[2])!==end)throw new Error('Invalid byte range response');
        const etag=response.headers.get('etag');
        if(!etag || etag.startsWith('W/'))throw new Error('Ranged download requires a strong ETag');
        if(known && (known.total!==Number(range[3]) || known.etag!==etag))throw new Error('Source version changed during ranged download');
        const data=Buffer.from(await response.arrayBuffer());
        if(data.length!==end-start+1)throw new Error('Truncated byte range');
        const entry={index,start,end,total:Number(range[3]),etag,url,final_url:response.url,
          retrieved_at:new Date().toISOString(),sha256:createHash('sha256').update(data).digest('hex'),bytes:data.length};
        const stem=String(index).padStart(6,'0');
        await fs.writeFile(path.join(parts,stem+'.bin'),data);
        await fs.writeFile(path.join(parts,stem+'.json'),JSON.stringify(entry)+'\n');
        return entry;
      })(),55000,()=>controller.abort());
  }
  if(!meta) {
    const first=await fetchChunk(0);
    meta={url,total:first.total,etag:first.etag,chunkBytes,first_retrieved_at:first.retrieved_at};
    await fs.writeFile(metaFile,JSON.stringify(meta,null,2)+'\n');
  }
  if(meta.url!==url||meta.chunkBytes!==chunkBytes)throw new Error('Mismatched resumed download');
  const count=Math.ceil(meta.total/chunkBytes);
  const existing=new Set((await fs.readdir(parts)).filter(p=>/^\d+\.json$/.test(p)).map(p=>Number(p.split('.')[0])));
  const missing=Array.from({length:count},(_,i)=>i).filter(i=>!existing.has(i)).slice(0,limit);
  let cursor=0;
  const errors=[];
  await Promise.all(Array.from({length:Math.min(concurrency,missing.length)},async()=>{
    while(cursor<missing.length) {
      const index=missing[cursor++];
      try { await fetchChunk(index,meta); } catch(e) { errors.push({index,error:String(e)}); }
    }
  }));
  const completed=(await fs.readdir(parts)).filter(p=>/^\d+\.json$/.test(p)).length;
  if(completed===count) {
    const buffers=[];
    const audit=[];
    for(let i=0;i<count;i++) {
      const stem=String(i).padStart(6,'0');
      const info=JSON.parse(await fs.readFile(path.join(parts,stem+'.json'),'utf8'));
      const data=await fs.readFile(path.join(parts,stem+'.bin'));
      if(info.etag!==meta.etag||info.total!==meta.total||createHash('sha256').update(data).digest('hex')!==info.sha256)throw new Error('Range checkpoint integrity mismatch');
      buffers.push(data); audit.push(info);
    }
    const combined=Buffer.concat(buffers);
    if(combined.length!==meta.total||combined.subarray(0,5).toString()!=='%PDF-')throw new Error('Invalid reassembled PDF');
    await fs.writeFile(target,combined);
    await fs.writeFile(target+'.acquisition.json',JSON.stringify({...meta,completed_at:new Date().toISOString(),sha256:createHash('sha256').update(combined).digest('hex'),ranges:audit},null,2)+'\n');
  }
  return {url,completed,chunks:count,bytes:meta.total,done:completed===count,errors};
}

if(typeof process!=='undefined' && process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  if(!process.argv[2])throw new Error('Supply absolute staging-directory');
  console.log(JSON.stringify(await downloadResources(path.dirname(fileURLToPath(import.meta.url)),process.argv[2]),null,2));
}
