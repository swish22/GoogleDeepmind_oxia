import requests
from urllib.parse import quote_plus

def fetch_nutritional_truth(ingredients: list[str]) -> dict:
    """Queries the HuggingFace Maressay dataset to find scientific nutritional matches."""
    results = []
    
    for ingredient in ingredients:
        # We only search the first few to avoid holding up the UI too long
        if len(results) >= 5: 
            break
            
        try:
            # Query the HuggingFace Datasets Server text search API
            url = f"https://datasets-server.huggingface.co/search?dataset=Maressay/food-nutrients-preparated&config=default&split=train&query={quote_plus(ingredient)}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                rows = data.get("rows", [])
                
                # If we found a row, extract the metadata
                if rows:
                    metadata = rows[0].get("row", {}).get("metadata", {})
                    recipe_ingredients = metadata.get("ingredients", [])
                    
                    # Try to find the specific ingredient match within the row's list
                    match = next((item for item in recipe_ingredients if ingredient.lower() in item.get("name", "").lower()), None)
                    
                    if match:
                        results.append({
                            "name": match.get("name"),
                            "calories": round(match.get("calories", 0), 2),
                            "protein": round(match.get("protein", 0), 2),
                            "carbs": round(match.get("carb", 0), 2),
                            "fat": round(match.get("fat", 0), 2),
                            "grams": round(match.get("grams", 0), 2)
                        })
                    elif recipe_ingredients:
                        # Fallback to the first ingredient in the matched row if no strict text match
                        first = recipe_ingredients[0]
                        results.append({
                            "name": first.get("name"),
                            "calories": round(first.get("calories", 0), 2),
                            "protein": round(first.get("protein", 0), 2),
                            "carbs": round(first.get("carb", 0), 2),
                            "fat": round(first.get("fat", 0), 2),
                            "grams": round(first.get("grams", 0), 2)
                        })
        except Exception as e:
            print(f"Dataset lookup failed for {ingredient}: {e}")
            continue
    
    # Retry failed lookups with simplified query (first word)
    if not results and ingredients:
        for ingredient in ingredients[:3]:
            if len(results) >= 5:
                break
            simplified = ingredient.split()[0] if ingredient else ""
            if not simplified:
                continue
            try:
                url = f"https://datasets-server.huggingface.co/search?dataset=Maressay/food-nutrients-preparated&config=default&split=train&query={quote_plus(simplified)}"
                res = requests.get(url, timeout=4)
                if res.status_code == 200:
                    data = res.json()
                    rows = data.get("rows", [])
                    if rows:
                        metadata = rows[0].get("row", {}).get("metadata", {})
                        recipe_ingredients = metadata.get("ingredients", [])
                        if recipe_ingredients:
                            first = recipe_ingredients[0]
                            results.append({
                                "name": first.get("name"),
                                "calories": round(first.get("calories", 0), 2),
                                "protein": round(first.get("protein", 0), 2),
                                "carbs": round(first.get("carb", 0), 2),
                                "fat": round(first.get("fat", 0), 2),
                                "grams": round(first.get("grams", 0), 2)
                            })
            except Exception:
                pass
            
    return {
        "dataset_matches": results,
        "source": "HuggingFace: Maressay/food-nutrients-preparated"
    }
