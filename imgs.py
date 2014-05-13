import requests
from requests.auth import HTTPBasicAuth
import json

def pp(j):
    print json.dumps(j,sort_keys=True,indent=4)
#params={'action':'query','list':'allimages','aiprop':'url','format':'json','aisort':'timestamp','aistart':'20131231000000','ailimit':'10'}
#params={'action':'query','list':'categorymembers','cmtitle':'Category:Featured_pictures','cmlimit':'500','format':'json'}

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


def createPayload(title,doctype):
    url='http://en.wikipedia.org/w/api.php'
    params={'action':'query','titles':title,'prop':'imageinfo','format':'json','iiprop':'url|size|dimensions|mime|mediatype|metadata|commonmetadata|extmetadata'}

    #timestamp|user|userid|comment|parsedcomment|canonicaltitle|url|size|dimensions|sha1|mime|thumbmime|mediatype|metadata|commonmetadata|extmetadata|archivename|bitdepth|uploadwarning
    r=requests.get(url,params=params)
    pp(r.json())
    try:
        thisurl=r.json()['query']['pages']['-1']['imageinfo'][0]['url']
        extmetadata=r.json()['query']['pages']['-1']['imageinfo'][0]['extmetadata']
        imagedescription=extmetadata['ImageDescription']['value']
        credit=extmetadata['Credit']['value']
        date=extmetadata['DateTimeOriginal']['value']
        payload={"entity-type": "document"}
        payload['name']=title 
        payload['type']=doctype
        payload['properties']={ 'dc:title':title, 'dc:description':'', 'dc:source':thisurl }
    except KeyError:
        return None
    return payload


def postDocToNuxeo(payload,url):
    auth=HTTPBasicAuth('Administrator', 'Administrator')
    headers={'content-type': 'application/json'}
    r=requests.post(url,data=json.dumps(payload),auth=auth,headers=headers)


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


def main():
    url='http://en.wikipedia.org/w/api.php'
    params={'action':'query','titles':'Albert Einstein','prop':'images','format':'json','imlimit':100}
    r=requests.get(url,params=params)
    for page in r.json()['query']['pages']:
        for image in r.json()['query']['pages'][page]['images']:
            payload=createPayload(image['title'],'OfflinePicture')
#            json.dumps(payload)
#            if payload:
#                postDocToNuxeo(payload,'http://localhost:8080/nuxeo/api/v1/path/default-domain/workspaces/OfflineEinstein')

#    out=postFilesToNuxeo(lst)
#    for i in out:
#        i['payload']['properties']['file:content']={ "upload-batch":"batch", "upload-fileId":i['index'] }
#        postDocToNuxeo(i['payload'],'http://localhost:8080/nuxeo/api/v1/path/default-domain/workspaces/Einstein')
    


#    requests.get('http://localhost:8080/nuxeo/api/v1/automation/batch/drop/batch')


#####  http://data.nasa.gov/great-images-in-nasa/

main()

