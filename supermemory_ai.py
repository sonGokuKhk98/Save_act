# pip install supermemory
from supermemory import Supermemory

client = Supermemory(
    api_key="sm_2d3AfLWkYYcRmzhuMdojsR_BAQeWQAGGVOZSATKBJEwumEzRIYoigLrMgvraVgPLKaciFsEQfmVGzbQyRXzMjRv",
    base_url="https://api.supermemory.ai/"
)

response = client.search.execute(
    q="What do you know about me?",
)
print(response.results)