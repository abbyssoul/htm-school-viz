import random
import json

import web
import numpy as np

from nupic.research.spatial_pooler import SpatialPooler as SP

global sp

urls = (
  "/", "Index",
  "/client/(.+)", "Client",
  "/_sp/", "SPInterface",
)
app = web.application(urls, globals())
render = web.template.render("tmpl/")


def templateNameToTitle(name):
  if name == "index": return ""
  title = name
  if "-" in title:
    title = title.replace("-", " ")
  return title.title()

class Index:

  def GET(self):
    with open("html/index.html", "r") as indexFile:
      return render.layout(
        "index",
        "HTM School Visualizations",
        indexFile.read()
      )

class Client:

  def GET(self, file):
    print file
    name = file.split(".")[0]
    path = "html/{}".format(file)
    with open(path, "r") as htmlFile:
      return render.layout(
        name,
        templateNameToTitle(name),
        htmlFile.read()
      )

class SPInterface:

  def POST(self):
    global sp
    params = json.loads(web.data())
    sp = SP(**params)
    web.header("Content-Type", "application/json")
    return json.dumps({"result": "success"})

  def PUT(self):
    requestInput = web.input()
    encoding = web.data()
    
    learn = True
    if "learn" in requestInput:
      learn = requestInput["learn"] == "true"

    getConnectedSynapses = False
    if "getConnectedSynapses" in requestInput:
      getConnectedSynapses = requestInput["getConnectedSynapses"] == "true"

    getPotentialPools = False
    if "getPotentialPools" in requestInput:
      getPotentialPools = requestInput["getPotentialPools"] == "true"
    
    activeCols = np.zeros(sp._numColumns, dtype="uint32")
    inputArray = np.array([int(bit) for bit in encoding.split(",")])

    print "SP compute: learning on? {}".format(learn)

    sp.compute(inputArray, learn, activeCols)
    web.header("Content-Type", "application/json")

    # Overlaps are cheap, so always return them. 
    overlaps = sp.getOverlaps()

    response = {
      "activeColumns": [int(bit) for bit in activeCols.tolist()],
      "overlaps": overlaps.tolist(),
    }

    # Connected synapses are not cheap, so only return when asked.
    if getConnectedSynapses:
      colConnectedSynapses = []
      for colIndex in range(0, sp.getNumColumns()):
        connectedSynapses = []
        connectedSynapseIndices = []
        sp.getConnectedSynapses(colIndex, connectedSynapses)
        for i, synapse in enumerate(connectedSynapses):
          if np.asscalar(synapse) == 1.0:
            connectedSynapseIndices.append(i)
        colConnectedSynapses.append(connectedSynapseIndices)
      response["connectedSynapses"] = colConnectedSynapses

    # Potential pools are not cheap either.
    if getPotentialPools:
      colPotentialPools = []
      for colIndex in range(0, sp.getNumColumns()):
        potentialPools = []
        potentialPoolsIndices = []
        sp.getPotential(colIndex, potentialPools)
        for i, pool in enumerate(potentialPools):
          if np.asscalar(pool) == 1.0:
            potentialPoolsIndices.append(i)
        colPotentialPools.append(potentialPoolsIndices)
      response["potentialPools"] = colPotentialPools

    return json.dumps(response)


if __name__ == "__main__":
  app.run()
