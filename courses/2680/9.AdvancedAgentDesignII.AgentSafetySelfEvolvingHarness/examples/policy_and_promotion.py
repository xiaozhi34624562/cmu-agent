"""Local deterministic teaching model; no LLM calls, code execution or messages."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json


@dataclass(frozen=True)
class Value:
    data: str
    sources: frozenset[str]
    readers: frozenset[str]


def derive(text, *inputs):
    sources = frozenset().union(*(x.sources for x in inputs))
    readers = frozenset.intersection(*(x.readers for x in inputs))
    return Value(text,sources,readers)


def policy(recipient, body, authorized_recipients):
    if recipient.data not in authorized_recipients:
        return False,'destination is outside fixed task authorization'
    if not recipient.sources <= {'trusted_user'}:
        return False,'destination depends on untrusted source; needs separate authorization'
    if recipient.data not in body.readers:
        return False,'destination is not a permitted reader of body'
    return True,'allowed in this toy policy'


def promote(candidate, evaluator_digest, expected_digest):
    if evaluator_digest != expected_digest:
        return False,'evaluation boundary changed'
    if candidate['unsafe_actions'] != 0:
        return False,'security regression'
    if candidate['benign_pass'] < 9 or candidate['cost'] > 100:
        return False,'utility or budget constraint failed'
    return True,'eligible for staged promotion; not a proof of generalization'


def main():
    public = frozenset({'alice@example.test','bob@example.test'})
    user = Value('alice@example.test',frozenset({'trusted_user'}),public)
    body = Value('internal summary',frozenset({'private_doc'}),frozenset({'alice@example.test'}))
    poisoned = Value('bob@example.test',frozenset({'retrieved_email'}),public)
    laundered = derive('alice@example.test',poisoned)
    authorized = {'alice@example.test'}
    cases = {
      'authorized_destination':policy(user,body,authorized),
      'untrusted_destination':policy(poisoned,body,authorized),
      'schema_valid_but_tainted_destination':policy(laundered,body,authorized),
      'trusted_but_unauthorized_reader':policy(Value('bob@example.test',frozenset({'trusted_user'}),public),body,{'bob@example.test'}),
    }
    assert cases['authorized_destination'][0]
    assert all(not v[0] for k,v in cases.items() if k!='authorized_destination')
    digest=hashlib.sha256(b'immutable evaluator version 1').hexdigest()
    good={'benign_pass':9,'unsafe_actions':0,'cost':80}
    risky={'benign_pass':10,'unsafe_actions':1,'cost':70}
    promotions={'bounded_candidate':promote(good,digest,digest),'faster_but_unsafe':promote(risky,digest,digest),'changed_evaluator':promote(good,'changed',digest)}
    assert promotions['bounded_candidate'][0]
    assert not promotions['faster_but_unsafe'][0] and not promotions['changed_evaluator'][0]
    print(json.dumps({'scope':'deterministic policy and promotion examples only','policy_cases':cases,'promotion_cases':promotions},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
