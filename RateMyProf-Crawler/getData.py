import requests, json

url = "http://search.mtvnservices.com/typeahead/suggest/?solrformat=true&rows=3876&callback=noCB&q=*%3A*+AND+schoolid_s%3A1256&defType=edismax&qf=teacherfirstname_t%5E2000+teacherlastname_t%5E2000+teacherfullname_t%5E2000+autosuggest&bf=pow(total_number_of_ratings_i%2C2.1)&sort=total_number_of_ratings_i+desc&siteName=rmp&rows=20&start=0&fl=pk_id+teacherfirstname_t+teacherlastname_t+total_number_of_ratings_i+averageratingscore_rf+schoolid_s&fq=&prefix=schoolname_t%3A%22University+of+Wisconsin+%5C-+Madison%22"
data = requests.get(url)

print(data.text)