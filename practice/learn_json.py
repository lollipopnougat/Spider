import json

dict={
    123:'244254',
    '999':123
}
with open('test.json','w') as f:
    print(json.dump(dict,f,indent=4))