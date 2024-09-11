# Travelmaxxing
Travelmaxxing generates cheap travel itineraries given a search criteria  

### Notes
Flight offers API returns flights in descending order of price. Hotel prices do not  
Hotel price API call can take several seconds, meaning it takes even longer to get through multiple batches  

### Todo
Frontend UI
Link to websites for booking flights and hotels  
Display multiple options for hotels instead of just the cheapest  

### Issues/Considerations
Flight departure date will not necessarily be the same as hotel checkin date due to flight time and timezone changes. Need to calculate arrival time?  
It might take too long to search every hotel. Is it enough to just search a few and hope a good enough price will be appear?  
It makes more sense to sort API call results by cost per day rather than just cost (for both flights and hotels)  