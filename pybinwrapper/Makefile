updatepybinwrapper: helloworld.gz.b64
	sed -i '/^run_compressed/d' pybinwrapper.py 
	echo -n "run_compressed(\"" >> pybinwrapper.py
	cat helloworld.gz.b64 | tr -d '\n' >> pybinwrapper.py
	echo "\")" >> pybinwrapper.py
helloworld.gz.b64: helloworld
	cat helloworld | gzip | base64 -w0 > helloworld.gz.b64
helloworld: helloworld.c
	gcc helloworld.c -o helloworld
clean:
	rm -f helloworld helloworld.gz.b64

