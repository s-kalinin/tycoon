#!/usr/bin/python3

import math
from random import random
import time
import potsdb
from collections import OrderedDict
import requests
import json

class Good:
  def __init__(self, gname='', gquantity=0.):
    self.gname=gname
    self.gquantity=gquantity

class Point:
  def __init__(self, pid=0, pname='', pcoords=[0,0], pconnections=[], pquantities=[0], pcapacity=0, pisHub=False):
    self.pid=pid
    self.pname=pname
    self.pcoords=pcoords
    self.pconnections=pconnections
    self.pquantities=pquantities
    self.pcapacity=pcapacity
    self.pisHub=pisHub
  def show(self):
    print(self.pname, self.pcoords, self.pquantities)

class Truck:
  def __init__(self, tid=0, tname='', tcoords=[0,0], tspeed=[1.,0.], tgoods=[], tplan={}, tcapacity=50, tquantity=0):
    self.tid=tid
    self.tname=tname
    self.tcoords=tcoords
    self.tspeed=tspeed
    self.tgoods=tgoods
    self.tplan=tplan
    self.tcapacity=tcapacity
    self.tquantity=tquantity
  def show(self):
    print('Truck info')
    print(self.tid,self.tcoords,[i.pname for i in self.tplan.keys()],'\n')

  def cycle_points(self):
    #print('Cycling plan:',self.tplan)
    #key=list(self.tplan.keys())[0]
    #value=self.tplan[key]
    #self.tplan.pop(key)
    #self.tplan[key]=value
    self.tplan.move_to_end(list(self.tplan.keys())[0])
    #print('New plan',list(self.tplan.keys())[0].pname)

def print_points():
  global points
  print('\nCurrent points')
  for p in points:
    p.show()
  print('---------------------\n')

def publish_points():
  global points
  print('Publish points status to OpenTSDB')
  #metrics = potsdb.Client('localhost', port=80, qsize=100000, host_tag=True, mps=10000, check_host=True)
  for p in points:
     print(p.pquantities[0],p.pname)
     data=('{"metric":"product0",'
          '"timestamp":"'+str(round(1000*time.time()))+'",'
          '"value":"'+str(p.pquantities[0])+'",'
          '"tags":{'
          '"host":"'+p.pname+'"'
          '}' # tags
          '}'
          )
     
     #data={'metric':'product0','timestamp':str(round(1000*time.time())),'tags':{'host':p.pname}}
     headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
     print(data)
     r = requests.post('http://localhost:4242/api/put',data=data,headers=headers)
     print(r.text)
     print(r.url)
     #print(metrics.send('product0',p.pquantities[0],host=p.pname))

  #metrics.wait()
  print('----------------------------------')

def update_points(updated_points):
   global points
   for p in updated_points:
     print('Updating', p.pname, p.pid)
     points[p.pid]=p

def customers_buy_goods():
   global points
   global buy_factor
   for p in range(len(points)):
     if points[p].pisHub or points[p].pquantities[0]<=0: continue
     # subtract a random number of goods
     bought=buy_factor*random()
     if points[p].pquantities[0] < bought: 
         points[p].pquantities[0]=0
     else: points[p].pquantities[0]-=bought

# initial definitions

a=Point(pid=0,pname='Hub',pcoords=[0,0],pconnections=[],pquantities=[10000],pcapacity=200,pisHub=True)
b=Point(pid=1,pname='B',pcoords=[3,3],pconnections=[],pquantities=[0],pcapacity=48,pisHub=False)
c=Point(pid=2,pname='C',pcoords=[-3,0],pconnections=[],pquantities=[0],pcapacity=52,pisHub=False)
d=Point(pid=3,pname='D',pcoords=[-3,-3],pconnections=[],pquantities=[0],pcapacity=100,pisHub=False)
e=Point(pid=4,pname='E',pcoords=[3,0],pconnections=[],pquantities=[0],pcapacity=50,pisHub=False)
points=[a,b,c,d,e]

truck1=Truck(tid=0,tname='T1',tcoords=a.pcoords,tspeed=[1.,0.],tgoods=[50],tplan=OrderedDict())
truck1.tplan[a]=0
truck1.tplan[b]=35
truck1.tplan[c]=10
truck2=Truck(tid=1,tname='T2',tcoords=a.pcoords,tspeed=[1.,0.],tgoods=[50],tplan=OrderedDict())
truck2.tplan[a]=0
truck2.tplan[d]=15
truck2.tplan[e]=20
trucks=[truck1,truck2]

pausetime=1
buy_factor=5.5
numberOfIterations=4500

# initial load of goods
for t in trucks:
  t.cycle_points()
  # (list(t.tplan.keys())[0] == next(iter(t.tplan))
  t.tspeed=[(list(t.tplan.keys())[0].pcoords[0]-list(t.tplan.keys())[-1].pcoords[0])/3,(list(t.tplan.keys())[0].pcoords[1]-list(t.tplan.keys())[-1].pcoords[1])/3]
  p=list(t.tplan.keys())[-1]
  print(p.pquantities)
  p.pquantities[0]-=t.tcapacity
  t.tquantity=t.tcapacity
  update_points([p])

print('Initial points status:')
print_points()

for i in range(1,numberOfIterations):
  time.sleep(pausetime)
  print('Iteration',i)
  for t in trucks:	
    t.tcoords=[ t.tcoords[j] + t.tspeed[j] for j in range(len(t.tspeed)) ]
    t.show()
    if t.tcoords == list(t.tplan.keys())[0].pcoords:
      p=list(t.tplan.keys())[0]
      print('delievered',t.tquantity)
      #print('Before updating:')
      #print_points(points)
      if p.pisHub:
          print('p is Hub')
          if p.pquantities[0] > t.tcapacity: 
              p.pquantities[0]-=t.tcapacity
              t.tquantity=t.tcapacity
          else:
              t.tquantity=p.pquantities[0]
              p.pquantities[0]=0
      else:
          #print('Adding',t.tquantity,'to',p.pname,p.pquantities[0])
          #print_points(points)
          #p.pquantities[0]+=t.tquantity
          #print('ccc',p.pquantities[0])
          #print_points(points)
          #t.tquantity=0
          pNewQuantity = p.pquantities[0] + t.tquantity
          if pNewQuantity <= p.pcapacity:
             p.pquantities[0] = pNewQuantity
             t.tquantity=0
          else:
             t.tquantity -= p.pcapacity-p.pquantities[0]
             p.pquantities[0] = p.pcapacity
      #print('aaa')
      #print_points(points)
      #print('bbb')
      update_points([p])
      print_points()
      print('change the plan')
      t.cycle_points()
      t.tspeed=[(list(t.tplan.keys())[0].pcoords[0]-list(t.tplan.keys())[-1].pcoords[0])/3,(list(t.tplan.keys())[0].pcoords[1]-list(t.tplan.keys())[-1].pcoords[1])/3]
      t.show()
      print('finished changing the plan')

  # Now customers buy goods
  customers_buy_goods()
  print('Customers bought')
  print_points()
  publish_points()
