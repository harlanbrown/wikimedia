import requests
from requests.auth import HTTPBasicAuth
import json

def pp(j):
    print json.dumps(j,sort_keys=True,indent=4)
#params={'action':'query','list':'allimages','aiprop':'url','format':'json','aisort':'timestamp','aistart':'20131231000000','ailimit':'10'}
#params={'action':'query','list':'categorymembers','cmtitle':'Category:Featured_pictures','cmlimit':'500','format':'json'}

url='http://en.wikipedia.org/w/api.php'
def getFile(url):
    fn=url.split('/')[-1]
    with open(fn, 'wb') as handle:
        response = requests.get(url, stream=True)
        if not response.ok:
	    print 'something went wrong'
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)

def getPayload(title):
    params={'action':'query','titles':title,'prop':'imageinfo','format':'json','iiprop':'url|extmetadata'}
    #timestamp|user|userid|comment|parsedcomment|canonicaltitle|url|size|dimensions|sha1|mime|thumbmime|mediatype|metadata|commonmetadata|extmetadata|archivename|bitdepth|uploadwarning
    r=requests.get(url,params=params)
    try:
        thisurl=r.json()['query']['pages']['-1']['imageinfo'][0]['url']
	extmetadata=r.json()['query']['pages']['-1']['imageinfo'][0]['extmetadata']
	imagedescription=extmetadata['ImageDescription']['value']
	credit=extmetadata['Credit']['value']
	date=extmetadata['DateTimeOriginal']['value']
	payload={"entity-type": "document"}
	payload['name']=title 
	payload['type']='Picture'#'OfflinePicture'
	payload['properties']={ 'dc:title':title, 'dc:description':'', 'dc:source':thisurl }
    except KeyError:
        return None
    return payload


def postDocToNuxeo(payload,url):
    auth = HTTPBasicAuth('Administrator', 'Administrator')
    headers = {'content-type': 'application/json'}
    r=requests.post(url,data=json.dumps(payload),auth=auth,headers=headers)
    print r.text


def postFilesToNuxeo(lst):
    uploadurl='http://localhost:8080/nuxeo/api/v1/automation/batch/upload'
    auth=HTTPBasicAuth('Administrator', 'Administrator')
    out=[]
    for idx,payload in enumerate(lst):
	name=payload['name']
	url=payload['properties']['dc:source']
	filename=url.split('/')[-1]
        # let's use tempfile and keep tabs on location of file
	getFile(url)
        headers = {'X-Batch-Id':'batch', 'X-File-Idx':idx, 'X-File-Name':filename}
	files = {'file': open(filename, 'rb')}
        r=requests.post(uploadurl,auth=auth,headers=headers,files=files)
	out.append({'index':idx,'payload':payload})
    return out 

# "file:content": { "upload-batch":"mybatchid", "upload-fileId":"0" }
#http://localhost:8080/nuxeo/site/automation/batch/files/batch
#http://localhost:8080/nuxeo/site/automation/batch/drop/batch



def main():
    params={'action':'query','titles':'Albert Einstein','prop':'images','format':'json','imlimit':50}
    r=requests.get(url,params=params)

    lst=[]
    
    for i in r.json()['query']['pages']:
        for j in r.json()['query']['pages'][i]['images']:
            title=j['title']
            payload=getPayload(title)
            if payload:
		lst.append(payload)
    out=postFilesToNuxeo(lst)
    for i in out:
        i['payload']['properties']['file:content']={ "upload-batch":"batch", "upload-fileId":i['index'] }
        postDocToNuxeo(i['payload'],'http://localhost:8080/nuxeo/api/v1/path/default-domain/workspaces/Einstein')


    
#    for i in lst:
#        postDocToNuxeo(json.dumps(i),'http://localhost:8080/nuxeo/api/v1/path/default-domain/workspaces/OfflineEinstein')
#    postFilesToNuxeo(lst)
#    postDocsToNuxeo(lst)


    requests.get('http://localhost:8080/nuxeo/api/v1/automation/batch/drop/batch')


main()

