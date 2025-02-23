from aind_scicomp_nautilex.lc_tools import query_docdb


query = {
  "data_description.project_name": "Thalamus in the middle",
  "$and": [
    {
      "acquisition.tiles.channel.channel_name": {
        "$regex": "^[0-9]+[.]0$"
      }
    },
    {
      "acquisition.tiles.channel.channel_name": {
        "$regex": "^[0-9]+$"
      }
    }
  ]
}

response = query_docdb.invoke(input={"query": query})

print(response)