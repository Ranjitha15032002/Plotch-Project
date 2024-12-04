# Shop Store
A comprehensive solution for fetching, categorizing, searching, and recommending products from Google Shopping.

## Application Features:
### Push Data to CatalogLake:
The application scrapes product details from Google Shopping and pushes them into CatalogLake using the GrocLake API.  
Product details include title, price, image URL, product link, and ratings.  
Logs the success or failure of the push operation for each product.

### Fetch Products from CatalogLake:
The app retrieves the list of products stored in CatalogLake, including details like groc_item_id and product names.  
Displays the fetched products in a web interface using a grid layout.

### Search Products:
Users can search for products using a search bar on the homepage.  
The search query is sent to the CatalogLake recommendation API, which uses semantic search to identify relevant products.

### Recommend Products:
Based on the user’s search query, the app recommends a matching product by:  
Fetching data from the CatalogLake recommendation engine.  
Displaying the product with its name, category, and image in the web interface.

### Background Caching:
A background scheduler runs daily at 6:00 AM to cache product data for quicker access and improved performance.  
Utilizes the apscheduler library to schedule tasks seamlessly.

## User-Friendly Interface:
### The frontend interface:
Built with TailwindCSS for responsiveness and modern design.  
Features a search bar and dynamically updated product grid to display fetched and recommended products.

## Technical Overview:
### FastAPI:
Backend framework for defining API endpoints.

### BeautifulSoup & httpx:
Web scraping and asynchronous HTTP requests for fetching product details.

### GrocLake API:
Integration for pushing, fetching, and recommending product data.

### HTML & TailwindCSS:
For creating a responsive and interactive user interface.

### apscheduler:
For scheduling the caching operation.
