

# tusd Protocol Usage Examples


Examples below were run using [httpie](https://httpie.org/) to query a local instance of the [official tusd (Go) server  implementation](https://github.com/tus/tusd), with http hooks activated: 

```
tusd -hooks-http http://127.0.0.1:8000/api/0.1/uploads/
``` 

A simple HTTP endpoint was set up to accept POST requests to the URL above, and provided naive, side-effects free hook implementations.

## Query server capabilities

The response header `Tus-Extension` indicates the extensions implemented by this `tusd` server implementation.

###Request:
```
http OPTIONS http://localhost:1080/files/ Tus-Resumable:1.0.0
```

###Response:
```
HTTP/1.1 200 OK
Content-Length: 0
Content-Type: text/plain; charset=utf-8
Date: Fri, 01 Dec 2017 11:40:28 GMT
Tus-Extension: creation,creation-with-upload,termination,concatenation
Tus-Resumable: 1.0.0
Tus-Version: 1.0.0
X-Content-Type-Options: nosniff
```

##Create new upload

We're uploading a file named 'file_sample.xml', 1820041 bytes in size.
Since `tusd` will store the uploaded data under a unique name it generates internally, we use the `Upload-Metadata` header to preserve any non-payload data about the upload.
Note that values in `Upload-Metadata` key-value pairs __must__ be base64 encoded.

###Request:
```
http POST http://localhost:1080/files/ \                                                                                                                                              1s 206ms
Tus-Resumable:1.0.0 \
Upload-Metadata:'filename ZmlsZV9zYW1wbGUueG1s' \
Upload-Length:1820041 \
Content-Type:application/offset+octet-stream
```
 
###Response:
```
HTTP/1.1 201 Created
Content-Length: 0
Content-Type: text/plain; charset=utf-8
Date: Fri, 01 Dec 2017 13:08:04 GMT
Location: http://localhost:1080/files/c71fc15b393082f889b16e2443ae41f4
Tus-Resumable: 1.0.0
Upload-Offset: 0
X-Content-Type-Options: nosniff
```

*__Note:__ the URL to use for actual data upload is indicated in the `Location` header.*

####Hooks triggered:

(body contents listed for each POST request received by the hooks HTTP server) 

__pre-create__ 
```
{'ID': '', 'Size': 1820041, 'Offset': 0, 'MetaData': {'filename': 'file_sample.xml'}, 'IsPartial': False, 'IsFinal': False, 'PartialUploads': None}
```

Note that at this stage the upload has not been yet issued an ID.
Assuming a positive response from the `pre-create` hook, the creation proceeds: 

__post-create__ 
```
{'ID': 'c71fc15b393082f889b16e2443ae41f4', 'Size': 1820041, 'Offset': 0, 'MetaData': {'filename': 'file_sample.xml'}, 'IsPartial': False, 'IsFinal': False, 'PartialUploads': None}
```

__post-receive__ 
```
{'ID': 'c71fc15b393082f889b16e2443ae41f4', 'Size': 1820041, 'Offset': 0, 'MetaData': {'filename': 'file_sample.xml'}, 'IsPartial': False, 'IsFinal': False, 'PartialUploads': None}
```

####Uploads storage
Upon a successful POST request, `tusd` will create a pair of `<ID>.bin` and `<ID>.info` files in its data directory. The former will store the upload's data, while the latter holds the upload's status and metadata. 


##A partial upload

We simulate an interrupted upload by sending our file without the last 41 bytes.
###Request:
```
head -c1820000 file_sample.xml | http PATCH http://localhost:1080/files/c71fc15b393082f889b16e2443ae41f4 \                                                                            1s 204ms
Tus-Resumable:1.0.0 \
Upload-Length:1820000 \
Upload-Offset:0 \
Content-Type:application/offset+octet-stream
```

###Response:
```
HTTP/1.1 204 No Content
Date: Fri, 01 Dec 2017 13:08:56 GMT
Tus-Resumable: 1.0.0
Upload-Offset: 1820000
X-Content-Type-Options: nosniff
```

####Hooks triggered

__post-receive__ 
```
{'ID': 'c71fc15b393082f889b16e2443ae41f4', 'Size': 1820041, 'Offset': 1820000, 'MetaData': {'filename': 'file_sample.xml'}, 'IsPartial': False, 'IsFinal': False, 'PartialUploads': None}
```

##Ask for status on the upload 

###Request:
```
http HEAD http://localhost:1080/files/c71fc15b393082f889b16e2443ae41f4 \
Tus-Resumable:1.0.0
```

###Response:
```
HTTP/1.1 200 OK
Cache-Control: no-store
Content-Type: text/plain; charset=utf-8
Date: Fri, 01 Dec 2017 13:09:12 GMT
Tus-Resumable: 1.0.0
Upload-Length: 1820041
Upload-Metadata: filename ZmlsZV9zYW1wbGUueG1s
Upload-Offset: 1820000
X-Content-Type-Options: nosniff
```


##Resume and finish the upload

We continue from the offset indicated by the server.

###Request:
```
tail -c+1820001 file_sample.xml | http PATCH http://localhost:1080/files/c71fc15b393082f889b16e2443ae41f4 \                                                                              566ms
Tus-Resumable:1.0.0 \
Upload-Length:41 \
Upload-Offset:1820000 \
Content-Type:application/offset+octet-stream
```

###Response:
```
HTTP/1.1 204 No Content
Date: Fri, 01 Dec 2017 13:09:58 GMT
Tus-Resumable: 1.0.0
Upload-Offset: 1820041
X-Content-Type-Options: nosniff
```

####Hooks triggered:

*__Note:__ While `tusd` will issue the `post-receive` event before `post-finish`, it's possible they will be received by the hooks target in reverse order.*

__post-receive__
```
{'ID': 'c71fc15b393082f889b16e2443ae41f4', 'Size': 1820041, 'Offset': 1820041, 'MetaData': {'filename': 'file_sample.xml'}, 'IsPartial': False, 'IsFinal': False, 'PartialUploads': None}
```

__post-finish__
```
{'ID': 'c71fc15b393082f889b16e2443ae41f4', 'Size': 1820041, 'Offset': 1820041, 'MetaData': {'filename': 'file_sample.xml'}, 'IsPartial': False, 'IsFinal': False, 'PartialUploads': None}
```

*__Note:__* *The `IsPartial`/`IsFinal` hook notification fields do __NOT__ indicate the actual completeness of a regular resumable upload, and are only relevant when using the `Concatenation` extension.*


##Delete an upload

*__Notes:__* 
 - This is refered to in the protocol spec as 'termination', which is NOT meant as finishing an upload.
 - Terminating an upload will cause `tusd` to delete the actual `.bin` and `.info` files from its data directory.
 The `post-finish` hook implementation must process the `.bin` file as required (e.g. move and rename it per the `Upload-Metadata` information),
 and only then issue the termination request. 

###Request:
```
http DELETE http://localhost:1080/files/c71fc15b393082f889b16e2443ae41f4 \
Tus-Resumable:1.0.0
```

###Response:
```
HTTP/1.1 204 No Content
Date: Fri, 01 Dec 2017 13:13:06 GMT
Tus-Resumable: 1.0.0
X-Content-Type-Options: nosniff
```

####Hooks triggered:

__post-terminate__ 
```
{'ID': 'c71fc15b393082f889b16e2443ae41f4', 'Size': 1820041, 'Offset': 0, 'MetaData': {'filename': 'file_sample.xml'}, 'IsPartial': False, 'IsFinal': False, 'PartialUploads': None}
```