Public IP Adress:  
	34.227.189.125

Google APIS used: 
	Google OAuth2 API 2 v2

Benchmarking setup:
	1)Start the main instance which is running the server via bottle
	2)Start a seperate instance by running the second_instance python file
	3)SSH into the second instance
	4)From here run the benchmark tests; this will give more accurate results than running the benchmarks locally
			The test to run is:
				ab -n 1000 -c xxx 34.227.189.125/?keywords=Key+word+here/
					Test 1000 requests and keep increasing number of concurrent users (xxx) until it fails