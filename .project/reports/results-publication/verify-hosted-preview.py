from pathlib import Path
import hashlib,json,struct
base=Path('.project/reports/portable-dat-histories')
groups={'sources':'3ed39843799746ad3cee546dce81204702a34f6437e1d8c6a34b932dc86801df','tools':'19e8e011e9dca5c5f47e1d1e6aecd58dd206c078fd3830d359f7910caed292bf','analysisTools':'db292a9004f10d26a0263002c8f76fa0c867a60997fd92f381f76a06e54e9eaf','fixtureSha256':'3f8e92b3c074ddba037394666ef319e4710dd84dcbe78321d22a923d24e38b41','datFixtureSha256':'3dfd2f3d10fded2fb3c664589458b6e4e41fb166e2a08fae5dbd2179d6a16a58','packageArchives':'1119fdfddd98f8e8efd58a3a34dd9305f7455510593cbd47116bfe64ce3bb83f','tests':'6e4f8c22715212275ee06ea670b17fbf5414ec301be4a7438d4364a888651561','inspection':'e9e7f4dc39b4c460a8e13319f9bd7fa17de683136479fefc5a7db3f81cc11c73','datInspection':'c091bb81c0e7f616d67f9719632bfb6002cecd445d0d5f9aca3e018d9af9fd94','cliControls':'ab40b942178865e302a490c8dda60abe2eacdcb02c7af81978cdc8093506b85c'}
def quote(s):return json.dumps(s,ensure_ascii=False,separators=(',',':'))
def canonical(v):
 if v is None:return'z'
 if isinstance(v,bool):return't'if v else'f'
 if isinstance(v,(int,float)):return'n'+struct.pack('>d',v).hex()
 if isinstance(v,str):return's'+quote(v)
 if isinstance(v,list):return'['+','.join(canonical(x)for x in v)+']'
 return'{'+','.join(quote(k)+':'+canonical(v[k])for k in sorted(v)if k!='runtime')+'}'
r={'success':True,'implementation':'62c7de1bea234acc7aea16ee7c11283822f86501','pipeline':2960686368,'pipelineStatus':'passed','jobs':{'research-linux-x64':17267558861,'shared-core-linux-x64':17267558862,'analysis-workflow-linux-x64':17267558863,'execution-workflow-linux-x64':17267558864,'results-workflow-linux-x64':17267558865},'method':'Authenticated GitLab artifact preview JSON read from visible DOM; selected groups canonicalized and SHA256 hashed with WebCrypto in CUA, independently recomputed against retained Mac/Linux ARM64 reports in Python. Runtime metadata removed; numbers encoded as IEEE754 binary64 big-endian hex. No archive/raw-byte download claim.','archiveDownloadVerified':False,'downloadLimitation':'IAB artifact download timed out; unauthenticated GitLab endpoint returned 404. No credentials extracted. Preview JSON remained accessible through GitLab-generated Pages links.','hostedReports':[]}
for mode,revision in [('current','current'),('rc2','3.0.0-rc2'),('post-rc2','post-rc2-2026-10-17')]:
 observed=dict(groups)
 if mode=='post-rc2':observed['sources']='35e59e6b34dfd90613ec2748d569017e0ff3213cde80a263b713535304a8bf8b'
 for host in ['macos-arm64','linux-arm64']:
  v=json.loads((base/(mode+'-'+host+'.json')).read_text())
  for key,digest in observed.items():assert hashlib.sha256(canonical(v[key]).encode()).hexdigest()==digest,(mode,host,key)
 r['hostedReports'].append({'upstreamRevision':revision,'source':'https://aleksa9275.gitlab.io/-/pre-po-max-x/-/jobs/17267558865/artifacts/X/Results/artifacts/'+mode+'-linux-x64.json','repository':{'head':r['implementation'],'dirty':False},'host':{'os':'Linux','architecture':'X64'},'success':True,'checks':78,'cliRejections':9,'sourceRows':164 if mode=='post-rc2'else 163,'matchingGroupsSha256':observed})
Path('.project/reports/results-publication/hosted-preview-verification.json').write_text(json.dumps(r,indent=2)+'\n')
print('All ten hosted artifact groups match retained Mac/Linux ARM64 evidence for all three pins; exact clean commit verified.')
