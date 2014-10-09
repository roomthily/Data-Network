#Packages
import requests
import ctypes
import json
import operator
from collections import defaultdict
import unicodedata
import collections
import subprocess
from nose.tools import with_setup
from rtree import index
from rtree.index import Rtree
from shapely.geometry import Polygon
import time
import codecs
import datetime
from datetime import timedelta
import Datanetwork
from Datanetwork import DataNetwork
import xml.etree.cElementTree as ET
from xml.etree.ElementTree import ElementTree
import igraph
from igraph import *
import copy
import itertools
from collections import OrderedDict

#General variables and their definitions
SpatialDict= {}
TemporalDict={} 
VariableDict={}
SI={} #Spatial Index it defiens the unique spatial Ids in a dictonary [Spatial ID: [list of data nodes], [location]]
TreeDict={} #store the spatial leafs in the form [leafID: [list of SI], [location]}
Spatial_OutList=[] #store spatial topological relationships
Temporal_OutList=[] #store temporal topolgical realtionships
Variable_OutList={}

'''Reading data of the sensors from the Seagrant project using their API/
    convert it to Json and store it in Dicts to assign IDs with data attributies'''

r=requests.get(r'http://seagrant.ncsa.illinois.edu/medici/api/geostreams/datapoints?geocode=44.33956524809713%2C-85.5703130364418%2C775.3611705566002&since=2009-01-01+12%3A00%3A00&until=2015-01-01+12%3A00%3A00&format=json') 

data=r.json()
data1=json.dumps(data) 
print '\n Number of data objects= ' +str(len(data)) 
  
#Superior=[-90,44,-84,48, 'Polygon','EPSG:2913'] may be used for testing case 
#SpatialDict[1000]=Superior 
  
'''Extracting the spatial, temporal, and variables attribuites and store them in 
a dicts spatial_dict[DataID: Type, Xmin, Ymin, Xmax, Ymax, SRID], 
tempral_dict[DataID: tstart,tend,tstep}, 
Variable_dict[DataID: V1,...]'''
  
for i, item in enumerate (data): 
    if len(data[i].get('geometry').get('coordinates')) <=4: # to check if a data entry is a point or a rectange and line/ the SRID is added manually 
           SpatialDict[data[i]['id']]=[data[i].get('geometry').get('coordinates')[0], 
                             data[i].get('geometry').get('coordinates')[1], 
                            data[i].get('geometry').get('coordinates')[0], 
                            data[i].get('geometry').get('coordinates')[1], 
                             unicodedata.normalize('NFKD', data[i].get('geometry').get('type')).encode('ascii','ignore'),'EPSG:2913']#epsg:26913 
    else: 
       SpatialDict[data[i]['id']]=[data[i].get('geometry').get('coordinates')[0], 
                      data[i].get('geometry').get('coordinates')[1], 
                      data[i].get('geometry').get('coordinates')[2], 
                      data[i].get('geometry').get('coordinates')[3], 
                      unicodedata.normalize('NFKD', data[i].get('geometry').get('type')).encode('ascii','ignore'),'epsg:26913'] 
    #Assumption timestep=0 and endtime=start time 
    TemporalDict[data[i]['id']]= [unicodedata.normalize('NFKD', data[i].get('start_time')).encode('ascii','ignore'),'0:0.0', 
                                  unicodedata.normalize('NFKD', data[i].get('end_time')).encode('ascii','ignore')] 
    Xx={} 
    for k,v in data[i].get('properties').iteritems(): 
        if not isinstance(v, str): 
            Xx[unicodedata.normalize('NFKD',k).encode('ascii','ignore')]= str(v) 
        else:     
            Xx[unicodedata.normalize('NFKD',k).encode('ascii','ignore')]=unicodedata.normalize('NFKD',v).encode('ascii','ignore') 
    Xx.pop('QC_ID',None) 
    Xx.pop('SAMPLE_ID',None) 
    Xx.pop('DEPTH_CODE',None)  
    VariableDict[data[i]['id']]= Xx 
  
  
print '\n Sample of the stored spatial data'
print SpatialDict[290341] 
print '\n Sample of the stored temporal data'
print TemporalDict[290341] 
print '\n Sample of the stored scientific data'
print VariableDict[290341] 



'''Development of spatial collections. The R-tree properties'''
p = index.Property()
p.set_near_minimum_overlap_factor(4)
p.set_leaf_capacity(25)
p.set_index_capacity(6)
tree=index.Rtree(properties=p)

SRID_Ref='EPSG:2913' #reference SRID

'''Groping of data entities that share the same spatial ID in dict SI [ID, coordinates]'''
C=DataNetwork.SpatialID(SpatialDict)

for i in range(len(C)): 
    lis=[]
    for k,v in SpatialDict.iteritems():
        if C[i]==v: lis.append(k)
    SI[i]=lis,C[i]
	 
            
'''Spatial normalization of data'''
for k, v in SI.iteritems():
    DataNetwork.SpatialProjection(SRID_Ref,SI[k][1])
    tree.add(k,(SI[k][1][0], SI[k][1][1],SI[k][1][2],SI[k][1][3]))
    
'''Temporal normalization of data'''
for k,v in TemporalDict.iteritems():
	TemporalDict[k]=[DataNetwork.isTimeFormat(TemporalDict[k][0]),TemporalDict[k][1],DataNetwork.isTimeFormat(TemporalDict[k][2])]

'''converting the R tree format from long to string and store in a new dic'''
Temp={}
for i in range(len(tree.leaves())):
	Temp[str(tree.leaves()[i][0])]=[map(str,tree.leaves()[i][1]),tree.leaves()[i][2]]

'''loop to prevent duplication of leafs resulting from leaf capacity limitation '''   
TreeDict={key: value for key, value in Temp.items() if value is not len(value)>0}
ID=0
for k in TreeDict.keys():
     TreeDict[ID] = TreeDict[k]
     del TreeDict[k]
     ID+=1
print ('\n Number of the tree leafs are: '+ str(len(TreeDict)))

#Superior lake intersection with Tree strucutre
lake=Polygon([(-93.0410161614418,46.43785689502422), (-93.0410161614418,49.06666839558117),
             (-84.4716802239418,49.06666839558117),(-84.47168022394,46.437856895024225),
             (-93.0410161614418,46.43785689502422)])
for k, v in TreeDict.iteritems():
    Polygon_0=Polygon([(TreeDict[k][1][0],TreeDict[k][1][1]),(TreeDict[k][1][2],TreeDict[k][1][1]),(TreeDict[k][1][2],TreeDict[k][1][3]),(TreeDict[k][1][0],TreeDict[k][1][3])])
    if lake.contains(Polygon_0):
        print ('\n Superior lake' + ':contains Saptial collection number' +str(k))
        print ('\n Number of SI capture in Superior lake: '+ str(len(TreeDict[k][0])))


'''Spatial toplogy between SI of the same Spatial collection'''
for k,v in TreeDict.iteritems():
    for i in range(len(v[0])):
        for j in range(len(v[0])):
            if i!=j:
                x= DataNetwork.SpatialToplogy(SI[int(TreeDict[k][0][i])][1],SI[int(TreeDict[k][0][j])][1])
                if not x == None: Spatial_OutList.append([i,x,j])
    print k
    print str(len(Spatial_OutList))

print ('\n Number of the spatial toplogy relationships are '+ str(len(Spatial_OutList)))
print ('\n sample of the spatial toplogy realtionships ' + str(Spatial_OutList[1]))
    
'''Temporal concatenation at each SI'''
for i in range(len(SI[1][0])):
    for j in range(len(SI[1][0])):
        if SI[1][0][i]!=SI[1][0][j] and VariableDict[SI[1][0][i]].keys()==VariableDict[SI[1][0][j]].keys():
            Temporal_OutList.append([SI[1][0][i],DataNetwork.TemporalReasoning(TemporalDict[SI[1][0][i]],TemporalDict[SI[1][0][j]]),SI[1][0][j]])
	
print ('\n Number of the Temporal toplogy relationships are '+ str(len(Temporal_OutList)))
print ('\n sample of the Temporal toplogy realtionships ' + str(Temporal_OutList[1]))
 
for k,v in TreeDict.iteritems():
     y=[]
     z=[]
     for i in range(len(v[0])):
        y=[VariableDict[x].keys() for x in SI[int(TreeDict[k][0][i])][0]]
        y.sort()
        z.append(list(y for y,_ in itertools.groupby(y)))
     z.sort()
     Variable_OutList[k]=list(OrderedDict.fromkeys(list(itertools.chain(*list(itertools.chain(*z))))))

                 


        
	

