from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
import httpx
import os
from groclake.cataloglake import CatalogLake
from dotenv import load_dotenv
load_dotenv()
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

#for lifespn
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startg schedulr
    print("Starting scheduler...")
    start_scheduler()
    yield
    #for cleaning
    print("Shutting down...")
app = FastAPI(lifespan=lifespan)
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
# GrocLake credentials
os.environ['GROCLAKE_API_KEY'] = os.getenv('GROCLAKE_API_KEY')
os.environ['GROCLAKE_ACCOUNT_ID'] = os.getenv('GROCLAKE_ACCOUNT_ID')

# Initialize GrocLake 
cataloglake = CatalogLake()


@app.get("/")
async def serve_homepage():
    with open("templates/index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@app.get("/fetch-products/")
async def fetch_products():
    # web scraping url
    base_url = "https://shopping.google.com/?pli=1"
    
    
    async with httpx.AsyncClient() as client:
        response = await client.get(base_url)
    
    if response.status_code != 200:
        return JSONResponse(status_code=500, content={"error": "Failed to fetch data from Google Shopping"})
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    items = []
    
    # scraping prodct detls
    for article in soup.find_all("article", class_="u3mD2d xwW5Ce"):
        try:
            # for title
            title_tag = article.find("h2", class_="MPhl6c")
            title = title_tag.text if title_tag else "N/A"
            
            # price
            price_tag = article.find("span", class_="aZK3gc")
            price = price_tag.text if price_tag else "N/A"
            
            # img url
            image_tag = article.find("img", class_="Ws3Esf")
            image_url = image_tag["src"] if image_tag and "src" in image_tag.attrs else "N/A"
            
            # prdct lnk
            link_tag = article.find("a", href=True)
            product_link = link_tag["href"] if link_tag else "N/A"
            
            # rtngs and rviews
            ratings_tag = article.find("span", class_="iu5UVe")
            ratings = ratings_tag.get("aria-label", "N/A") if ratings_tag else "N/A"
            
            items.append({
                "title": title,
                "price": price,
                "image_url": image_url,
                "product_link": f"https://shopping.google.com{product_link}",
                "ratings": ratings,
            })
        except AttributeError:
            
            continue
    
    return {"products": items}

#fectng to catagolake
@app.get("/push_product_cataloglake/")
async def push_cataloglake():
    
    fetched_products = await fetch_products()
    print("Fetched products:", fetched_products)
    products = fetched_products.get("products", [])

    if not products:
        raise HTTPException(status_code=404, detail="No products found to push to CatalogLake")

    # for trckng if product pushed or no
    success_responses = []
    failed_products = []

    
    for product in products:
       
        # Mapping prodct
       
        product_create_request = {
            "product_name_hint": product["title"],
            "category_name_hint": product["title"],
            "provider_name_hint": "RandomSeller",
            "images": [
                {
                    "image_name": product["title"],
                    "image_url": product["image_url"]
                }
            ]
        }

        try:
            # Pushing each prdct to CatalogLake
            catalog_push_request = cataloglake.gen(product_create_request)
            print(catalog_push_request)
            print("PUSHED")
            success_responses.append({
                "product_title": product["title"],
                "response": catalog_push_request
            }
            )#if not pushed
        except Exception as e:
            
            failed_products.append({
                "product_title": product["title"],
                "error": str(e)
            })

    # for our convenience (details)
    return {
        "success_count": len(success_responses),
        "failed_count": len(failed_products),
        "success_responses": success_responses,
        "failed_products": failed_products
    }

@app.get("/fetch_product_cataloglake/")
async def fetch_product_cataloglake():
    
    product_fetch_request = {
        
        "groc_item_id": "",
        "groc_category": "",
        "is_in_stock": "",
        "page_size": "50",
        "page_number": "1"
    }

    try:
    
        catalog_fetch_product = cataloglake.fetch(product_fetch_request)

        
        groc_item_ids = []
        items = catalog_fetch_product.get('items', [])

        
        for item in items:
            print(item['groc_item_id'], ' : ', item['name'])
            groc_item_ids.append(item['groc_item_id'])

        # (in log)
        if items:
            print("First catalog_fetch_data:", items[0]['groc_item_id'])
        print("Length of catalog:", len(items))
        print(f"Catalog fetch product response: {catalog_fetch_product}")
        print(f"Groc Item IDs: {groc_item_ids}")

        
        return {
            "message": "Fetched products successfully",
            "total_items": len(items),
            "groc_item_ids": groc_item_ids,
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from CatalogLake: {str(e)}")


async def cache_catalog_data():
    try:
        data=await fetch_product_cataloglake()
        groc_item_ids = data.groc_item_ids  
        product_cache_request = {"groc_item_id": groc_item_ids}
        print(f"Requesting cache for: {product_cache_request}")

        
        catalog_cache_product = await cataloglake.cache(product_cache_request)
        print("catalog_cache_data:", catalog_cache_product)
    except Exception as e:
        print("Error caching data:", str(e))

@app.get("/recommend_products")
def recommend_products(search_term: str):
    print("search term is", search_term)
    
    product_search_request = {
  "query":search_term,
 "search_type": "semantic",
 "image_url": "",
  "price": 599,
  "image_bytes": "898988CVFIFASS",
 "cataloglake_id": "y86yvr1yhleo9c86"
}
    
    try:
        # Call the cataloglake recommendation API
        
        catalog_recommend_product =cataloglake.search(product_search_request)
        
       
        
    
        if 'items' not in catalog_recommend_product:
            raise HTTPException(status_code=404, detail="No products found for the given search term.")
        
        # Return the product items
        print("recomnede search prod is",catalog_recommend_product['items'][0])
        return {"items": catalog_recommend_product['items'][0]}
    
    except Exception as e:
        print(f"Error fetching recommended products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching recommended products: {str(e)}")



# Settng up schedular
def start_scheduler():
    scheduler = BackgroundScheduler()
    trigger = CronTrigger(hour=6, minute=0)  
    scheduler.add_job(
        func=lambda: asyncio.run(cache_catalog_data()), 
        trigger=trigger, 
        id="cache_catalog_data_job",
        replace_existing=True
    )
    scheduler.start()







if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
