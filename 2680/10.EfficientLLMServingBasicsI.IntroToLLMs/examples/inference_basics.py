"""CPU teaching checks; no model inference or GPU benchmark is performed."""
import json
import math
import random


def softmax(xs):
    peak = max(xs)
    ys = [math.exp(x - peak) for x in xs]
    return [y / sum(ys) for y in ys]


def attend(q, keys, values):
    probs = softmax([sum(a*b for a,b in zip(q,k))/math.sqrt(len(q)) for k in keys])
    return [sum(p*v[j] for p,v in zip(probs,values)) for j in range(len(values[0]))]


def project(x, weights):
    return [sum(a*b for a,b in zip(x,column)) for column in zip(*weights)]


def cached_equivalence():
    rng = random.Random(7)
    xs = [[rng.uniform(-1,1) for _ in range(4)] for _ in range(6)]
    mats = [[[rng.uniform(-1,1) for _ in range(4)] for _ in range(4)] for _ in range(3)]
    keys, values, largest_error = [], [], 0.0
    for i,x in enumerate(xs):
        q = project(x,mats[0]); keys.append(project(x,mats[1])); values.append(project(x,mats[2]))
        cached = attend(q,keys,values)
        full = attend(q,[project(z,mats[1]) for z in xs[:i+1]],[project(z,mats[2]) for z in xs[:i+1]])
        largest_error = max(largest_error,max(abs(a-b) for a,b in zip(cached,full)))
    assert largest_error < 1e-12
    return largest_error


def main():
    d,l,h,hkv,dk,dff,v = 8192,80,64,8,128,28672,128256
    n,b = 80000,64
    attention = 2*d*h*dk + 2*d*hkv*dk
    ffn = 3*d*dff
    params = l*(attention+ffn)+2*v*d
    kv = 2*l*hkv*dk*2
    result = {
        'scope':'CPU arithmetic and one-head cache equivalence only',
        'params_without_norms':params,
        'kv_bytes_per_token':kv,
        'kv_KiB_per_token':kv/1024,
        'weights_GB_using_70_6B':70.6e9*2/1e9,
        'one_80k_request_total_GB':(70.6e9*2+n*kv)/1e9,
        'sixty_four_80k_requests_total_GB':(70.6e9*2+b*n*kv)/1e9,
        'ideal_80k_prefill_seconds':(2*70.6e9*n+2*l*d*n*n)/1.978e15,
        'all_layers_scores_GB':8192**2*h*l*2/1e9,
        'one_layer_scores_GB':8192**2*h*2/1e9,
        'cache_equivalence_max_abs_error':cached_equivalence(),
    }
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
