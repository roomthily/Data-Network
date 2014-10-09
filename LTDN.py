#Packages
import os
import json
import subprocess
from nose.tools import with_setup
from shapely.geometry import Point
from shapely.geometry import LineString
from shapely.geometry import Polygon
from shapely.geometry import shape
import pyproj
from pyproj import Proj, transform
import unicodedata
import collections 
import time
import datetime
from datetime import timedelta
import itertools
import re

class DataNetwork(object):

    
    @staticmethod
    def convert(data):
      if isinstance(data, unicode):
        return str(data)
      elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
      elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
      else:
        return data
    
    @staticmethod
    def SpatialID(SpatialDict):
        vals=SpatialDict.values()
        vals.sort()
        valz=list(vals for vals,_ in itertools.groupby(vals))
        return valz
    
    @staticmethod
    def SpatialProjection(SRID_Ref,SRID_Org):
        target_epsg=pyproj.Proj(init=SRID_Ref)
        if SRID_Org[5] != SRID_Ref:
            origin_epsg=pyproj.Proj(init=SRID_Org[5])        
            g1=transform(target_epsg,origin_epsg,SRID_Org[0],SRID_Org[1])
            g2=transform(target_epsg,origin_epsg,SRID_Org[2],SRID_Org[3])
            SRID_Org[0]=g1[0]
            SRID_Org[1]=g1[1]
            SRID_Org[2]=g2[1]  
            SRID_Org[3]=g2[1]
            SRID_Org[5]=SRID_Ref
            return SRID_Org
        
    @staticmethod
    def SpatialToplogy (Spatial_A,Spatial_B):
               if Spatial_A[4] == 'Point' and Spatial_B[4]== 'Point':
                 Point_0=Point(Spatial_A[0],Spatial_A[1])
                 Point_1=Point(Spatial_B[0],Spatial_B[1])
                 #Point to point relationships
                 if Point_0.equals(Point_1): return 'Point1 equals Point2'
                 if Point_0.within(Point_1.buffer(2)): return 'Point1 lies within a buffer of 2 m from Point2'
                 if Point_0.overlaps(Point_1): return 'Point1 overlaps Point2'
                 #if Point_0.disjoint(Point_1): return 'Point1 disjoint Point2'
                 
                 #Point to line relationships
               if Spatial_A[4] == 'Point' and Spatial_B[4]== 'Line':
                    Point_0=Point(Spatial_A[0],Spatial_A[1])
                    Line_0=LineString([(Spatial_B[0],Spatial_B[1]),(Spatial_B[2],Spatial_B[3])])
                    if Point_0.touches(Line_0):return 'Point1 touches Line1'
                    if Point_0.within(Line_0.buffer(2)):return 'Point1 lies within a buffer of 2 m from L1'
                 #Point to polygon relationships
               if Spatial_A[4] == 'Point' and Spatial_B[4]== 'Polygon':
                    Point_0=Point(Spatial_A[0],Spatial_A[1])
                    Polygon_0=Polygon([(Spatial_B[0],Spatial_B[1]),(Spatial_B[2],Spatial_B[1]),(Spatial_B[2],Spatial_B[3]),(Spatial_B[0],Spatial_B[3])])
                    if Point_0.touches(Polygon_0):return 'Point1 touches Polygon1'
                    if Point_0.within(Polygon_0):return'Point1 lies within Polygon1'
                    if Point_0.overlaps(Polygon_0):return 'Point1 lies overlaps Polygon1'
                #Line to line relationships
               if Spatial_A[4]=='Line' and Spatial_B[4]=='Line':
                    Line_0=LineString([(Spatial_A[0],Spatial_A[1]),(Spatial_A[2],Spatial_A[3])])
                    Line_1=LineString([(Spatial_B[0],Spatial_B[1]),(Spatial_B[2],Spatial_B[3])])
                    if Line_0.equals(Line_1):return 'Line0 equals Line1'
                    if Line_0.touches(Line_1):return 'Line0 touches Line1'
                    if Line_0.crosses(Line_1):return 'Line0 crosses Line1'
                    if Line_0.within(Line_1.buffer(2)):return 'Line0 lies within a buffer of 2 m Line1'
                    if Line_0.overlaps(Line_1):return 'Line0 overlaps Line1'
                 #Line to polygon relationships  
               if Spatial_A[4]=='Line' and Spatial_B[4]=='Polygon':
                    Line_0=LineString([(Spatial_A[0],Spatial_A[1]),(Spatial_A[2],Spatial_A[3])])
                    Polygon_0=Polygon([(Spatial_B[0],Spatial_B[1]),(Spatial_B[2],Spatial_B[1]),(Spatial_B[2],Spatial_B[3]),(Spatial_B[0],Spatial_B[3])])
                    if Line_0.touches(Polygon_0):return 'Line0 touches Polygon1'
                    if Line_0.crosses(Polygon_0):return 'Line0 crosses Polygon1'
                    if Line_0.within(Polygon_0):return 'Line0 lies within Polygon1'
                 #Polygon to Polygon relationships
               if Spatial_A[4]=='Polygon' and Spatial_B[4]=='Polygon':
                    Polygon_0=Polygon([(Spatial_A[0],Spatial_A[1]),(Spatial_A[2],Spatial_A[1]),(Spatial_A[2],Spatial_A[3]),(Spatial_A[0],Spatial_A[3])])
                    Polygon_1=Polygon([(Spatial_B[0],Spatial_B[1]),(Spatial_B[2],Spatial_B[1]),(Spatial_B[2],Spatial_B[3]),(Spatial_B[0],Spatial_B[3])])
                    if Polygon_0.touches(Polygon_1):return 'Polygon touches Polygon1'
                    if Polygon_0.equals(Polygon_1):return 'Polygon0 equals Polygon1'
                    if Polygon_0.within(Polygon_1):return 'Polygon lies within Polygon1'
                    if Polygon_0.within(Polygon_1.buffer(2)):return 'Polygon lies within a buffer of 2m  Polygon1'
               #else:
                 #  return None
    @staticmethod
    def isTimeFormat(T):
      try:  
         time.strptime(T, "%Y-%m-%d %H:%M:%S-%f")
         return T
      except:
         X=re.sub('[.]','-',T)
         return X

    @staticmethod
    def TemporalReasoning(T1, T2):
        #converting the first time
        TimeA_start=T1[0]#atetime.datetime.strptime(T1[0],"%Y-%m-%d %H:%M:%S-%f")
        TimeA_step=T1[1]#datetime.datetime.strptime(T1[1],"%M:%S.%f")
        TimeA_end=T1[2]#datetime.datetime.strptime(T1[2],"%Y-%m-%d %H:%M:%S-%f")
    
        #converting the second time
        TimeB_start=T2[0]#datetime.datetime.strptime(T2[0],"%Y-%m-%d %H:%M:%S-%f")
        TimeB_step=T2[1]#datetime.datetime.strptime(T2[1],"%M:%S.%f")
        TimeB_end=T2[2]#datetime.datetime.strptime(T2[2],"%Y-%m-%d %H:%M:%S-%f")
   
        if TimeA_start==TimeB_start and TimeA_end==TimeB_end and TimeA_step==TimeB_step: return 'T1 e with the same frequency T2'
        if TimeA_start==TimeB_start and TimeA_end==TimeB_end and TimeA_step>TimeB_step: return 'T1 e with the higher frequency T2'
        if TimeA_start==TimeB_start and TimeA_end==TimeB_end and TimeA_step<TimeB_step: return 'T1 e with the lower frequency T2'
        
        if TimeA_end<TimeB_start and TimeA_end==TimeB_end and TimeA_step==TimeB_step: return 'T1 p with the same frequency T2'
        if TimeA_end<TimeB_start and TimeA_end==TimeB_end and TimeA_step>TimeB_step: return 'T1 p with the higher frequency T2'
        if TimeA_end<TimeB_start and TimeA_end==TimeB_end and TimeA_step<TimeB_step: return 'T1 p with the lower frequency T2'
          
        if TimeA_start<TimeB_start and TimeA_end==TimeB_end and TimeA_step==TimeB_step:return 'T1 m  with the same frequency T2 and T2 mi T1'
        if TimeA_start<TimeB_start and TimeA_end==TimeB_end and TimeA_step>TimeB_step:return 'T1 m with the higher frequency T2 and T2 mi T1'
        if TimeA_start<TimeB_start and TimeA_end==TimeB_end and TimeA_step<TimeB_step:return 'T1 m with the lower frequency T2 and T2 mi T1'
        
        if TimeA_start<TimeB_start and TimeB_start<TimeA_end<TimeB_end and TimeA_step==TimeB_step: return 'T1 o with the same frequency T2 and T2 o T1'
        if TimeA_start<TimeB_start and TimeB_start<TimeA_end<TimeB_end and TimeA_step>TimeB_step: return 'T1 o with the higher frequency T2 and T2 o T1'
        if TimeA_start<TimeB_start and TimeB_start<TimeA_end<TimeB_end: return 'T1 o with the lower frequency T2 and T2 o T1'
        
        if TimeA_start==TimeB_start and TimeB_start<TimeA_end<TimeB_end and TimeA_step==TimeB_step: return 'T1 s with the same frequency T2 and T2 si T1'
        if TimeA_start==TimeB_start and TimeB_start<TimeA_end<TimeB_end and TimeA_step>TimeB_step: return 'T1 s with the higher frequency T2 and T2 si T1'
        if TimeA_start==TimeB_start and TimeB_start<TimeA_end<TimeB_end and TimeA_step<TimeB_step: return 'T1 s with the lower frequency  T2 and T2 si T1'
        
        if TimeA_end==TimeB_end and TimeB_start<TimeA_start<TimeB_end and TimeA_step==TimeB_step: return 'T1 f with the same frequency T2 and T2 fi T1'
        if TimeA_end==TimeB_end and TimeB_start<TimeA_start<TimeB_end and TimeA_step>TimeB_step: return 'T1 f with the higher frequency T2 and T2 fi T1'
        if TimeA_end==TimeB_end and TimeB_start<TimeA_start<TimeB_end and TimeA_step<TimeB_step: return 'T1 f with the lower frequency T2 and T2 fi T1'
        
        if TimeA_start<TimeB_start and TimeA_end<TimeB_end and TimeA_step==TimeB_step: return 'T1 di with the same frequency T2 and T2 d with the same frequency T1'
        if TimeA_start<TimeB_start and TimeA_end<TimeB_end and TimeA_step>TimeB_step: return 'T1 di T2 with the higher frequency and T2 d T1'
        if TimeA_start<TimeB_start and TimeA_end<TimeB_end and TimeA_step<TimeB_step: return 'T1 di with the lower frequency  T2 and T2 d T1'
                
               


    

