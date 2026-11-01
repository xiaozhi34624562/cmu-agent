"""CPU-only teaching calculations: no CUDA kernel or performance measurement."""
import json
import math
import random


def direct(scores, values):
    peak = max(scores)
    weights = [math.exp(s-peak) for s in scores]
    return [sum(w*v[j] for w,v in zip(weights,values))/sum(weights) for j in range(len(values[0]))]


def online(scores, values, tile):
    m, total = -math.inf, 0.0
    numerator = [0.0]*len(values[0])
    for start in range(0,len(scores),tile):
        s, vs = scores[start:start+tile], values[start:start+tile]
        new_m = max(m,max(s))
        scale = math.exp(m-new_m)
        exps = [math.exp(x-new_m) for x in s]
        total = scale*total + sum(exps)
        numerator = [scale*a+sum(w*v[j] for w,v in zip(exps,vs)) for j,a in enumerate(numerator)]
        m = new_m
    return [x/total for x in numerator]


def main():
    peak,bw = 989e12,4.8e12
    rng = random.Random(42)
    scores = [rng.uniform(-40,40) for _ in range(17)]
    values = [[rng.uniform(-1,1) for _ in range(5)] for _ in scores]
    baseline = direct(scores,values)
    errors = {str(t):max(abs(a-b) for a,b in zip(baseline,online(scores,values,t))) for t in [1,2,4,8,17]}
    assert max(errors.values()) < 1e-12
    n,d,l,batch,hkv,dk = 32768,4096,32,16,8,128
    kv = 2*l*hkv*dk*2
    weights = 16.1e9
    result = {
        'scope':'analytical H200 ideal bounds and CPU FP64 online-softmax equivalence only',
        'ridge_FLOP_per_byte':peak/bw,
        'batch1_weight_GEMV_percent_peak':bw/peak*100,
        'pipeline_bytes_total_at_250ns':bw*250e-9,
        'pipeline_bytes_per_SM_132':bw*250e-9/132,
        'llama8b_KV_bytes_per_token':kv,
        'batch16_context32768_KV_GB':batch*n*kv/1e9,
        'batch16_context32768_step_read_lower_bound_ms':(weights+batch*n*kv)/bw*1000,
        'gemv_weight_only_AI_BF16_by_batch':{str(b):float(b) for b in [1,8,32,128,256]},
        'online_softmax_max_abs_errors':errors,
        'amdahl_attention30percent_kernel2x_speedup':1/(0.7+0.3/2),
    }
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
