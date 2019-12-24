#! /usr/bin/env python -t
'''
Generates Inkscape SVG file containing box components needed to 
laser cut a tabbed construction box taking kerf and clearance into account

Copyright (C) 2011 elliot white

Changelog:
19/12/2014 Paul Hutchison:
 - Ability to generate 6, 5, 4, 3 or 2-panel cutouts
 - Ability to also generate evenly spaced dividers within the box
   including tabbed joints to box sides and slots to slot into each other
   
23/06/2015 by Paul Hutchison:
 - Updated for Inkscape's 0.91 breaking change (unittouu)
 
v0.93 - 15/8/2016 by Paul Hutchison:
 - Added Hairline option and fixed open box height bug
 
v0.94 - 05/01/2017 by Paul Hutchison:
 - Added option for keying dividers into walls/floor/none

v0.95 - 16/11/2019 by Marc Winoto
- Updated to work with Inkscape 1.0 Beta

This program is ugly software: you can clean it up yourself and/or mock it 
under the unpublished terms of common civility.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = "0.95" ### please report bugs, suggestions etc at https://github.com/paulh-rnd/TabbedBoxMaker ###

import math
import os
import sys
import inkex
from inkex import localization as localization
localization.localize()

debug = True
# Global variables
parent = None
linethickness = None #1 # default unless overridden by settings
materialThickness = None #3
nomTab = None #6
equalTabs = None #0
divx = None #25
divy = None #25
kerf = None #0.5
clearance = None #0.01
correction = None #kerf-clearance
hairline = None 
keydivwalls = None #0
keydivfloor = None #0
hp = None #0

def log(text):
  if 'SCHROFF_LOG' in os.environ:
    f = open(os.environ.get('SCHROFF_LOG'), 'a')
    f.write(text + "\n")

def debug(text):
  if debug:
      inkex.utils.debug(text)

def drawS(XYstring):         # Draw lines from a list
  name='part'
  style = { 'stroke': '#000000', 'stroke-width'  : str(linethickness), 'fill': 'none' }
  drw = {'style':str(inkex.Style(style)),inkex.addNS('label','inkscape'):name,'d':XYstring}
  inkex.elements.etree.SubElement(parent, inkex.addNS('path','svg'), drw )
  return

# jslee - shamelessly adapted from sample code on below Inkscape wiki page 2015-07-28
# http://wiki.inkscape.org/wiki/index.php/Generating_objects_from_extensions

def drawCircle(r, coords):
    log("putting circle at (%d,%d)" % coords)
    style = {'stroke': '#000000',
             'stroke-width': str(linethickness), 'fill': 'none'}
    ell_attribs = {'style': str(inkex.Style(style)),
                   inkex.addNS('cx', 'sodipodi'): str(coords[0]),
                   inkex.addNS('cy', 'sodipodi'): str(coords[1]),
                   inkex.addNS('rx', 'sodipodi'): str(r),
                   inkex.addNS('ry', 'sodipodi'): str(r),
                   inkex.addNS('start', 'sodipodi'): str(0),
                   inkex.addNS('end', 'sodipodi'): str(2*math.pi),
                   # all ellipse sectors we will draw are open
                   inkex.addNS('open', 'sodipodi'): 'true',
                   inkex.addNS('type', 'sodipodi'): 'arc',
                   'transform': ''}
    inkex.elements.etree.SubElement(
        parent, inkex.addNS('path', 'svg'), ell_attribs)

def side(rxy,soxy,eoxy,tabVec,length,dirxy,isTab,isDivider,numDividers,divSpacing,divOffset):
  #      root startOffset endOffset tabVec length  direction  isTab isDivider numDividers divSpacing dividerOffset

  divs = int(length/nomTab)  # divisions
  if not divs % 2:
    divs -= 1   # make divs odd
  divs = float(divs)
  tabs = (divs-1)/2          # tabs for side
  
  if equalTabs:
    gapWidth=tabWidth=length/divs
  else:
    tabWidth=nomTab
    gapWidth=(length-tabs*nomTab)/(divs-tabs)
    
  if isTab:                 # kerf correction
    gapWidth-=correction
    tabWidth+=correction
    first=correction/2
  else:
    gapWidth+=correction
    tabWidth-=correction
    first=-correction/2
    
  s=[] 
  h=[]
  firstVec=0; secondVec=tabVec
  dirxN=0 if dirxy[0] else 1 # used to select operation on x or y
  diryN=0 if dirxy[1] else 1
  (Vx,Vy)=(rxy[0]+soxy[0]*materialThickness,rxy[1]+soxy[1]*materialThickness)
  s='M '+str(Vx)+','+str(Vy)+' '

  if dirxN: Vy=rxy[1] # set correct line start
  if diryN: Vx=rxy[0]

  # generate line as tab or hole using:
  #   last co-ord:Vx,Vy ; tab dir:tabVec  ; direction:dirx,diry ; thickness:thickness
  #   divisions:divs ; gap width:gapWidth ; tab width:tabWidth

  for n in range(1,int(divs)):
    if ((n%2) ^ (not isTab)) and numDividers>0 and not isDivider: # draw holes for divider joints in side walls
      w=gapWidth if isTab else tabWidth
      if n==1:
        w-=soxy[0]*materialThickness
      for m in range(1,int(numDividers)+1):
        Dx=Vx+-dirxy[1]*divSpacing*m
        Dy=Vy+dirxy[0]*divSpacing*m
        if n==1:
          Dx+=soxy[0]*materialThickness
        h='M '+str(Dx)+','+str(Dy)+' '
        Dx=Dx+dirxy[0]*w+dirxN*firstVec+first*dirxy[0]
        Dy=Dy+dirxy[1]*w+diryN*firstVec+first*dirxy[1]
        h+='L '+str(Dx)+','+str(Dy)+' '
        Dx=Dx+dirxN*secondVec
        Dy=Dy+diryN*secondVec
        h+='L '+str(Dx)+','+str(Dy)+' '
        Dx=Dx-(dirxy[0]*w+dirxN*firstVec+first*dirxy[0])
        Dy=Dy-(dirxy[1]*w+diryN*firstVec+first*dirxy[1])
        h+='L '+str(Dx)+','+str(Dy)+' '
        Dx=Dx-dirxN*secondVec
        Dy=Dy-diryN*secondVec
        h+='L '+str(Dx)+','+str(Dy)+' '
        drawS(h)
    if n%2:
      if n==1 and numDividers>0 and isDivider: # draw slots for dividers to slot into each other
        for m in range(1,int(numDividers)+1):
          Dx=Vx+-dirxy[1]*(divSpacing*m+divOffset)
          Dy=Vy+dirxy[0]*(divSpacing*m-divOffset)
          h='M '+str(Dx)+','+str(Dy)+' '
          Dx=Dx+dirxy[0]*(first+length/2)
          Dy=Dy+dirxy[1]*(first+length/2)
          h+='L '+str(Dx)+','+str(Dy)+' '
          Dx=Dx+dirxN*materialThickness
          Dy=Dy+diryN*materialThickness
          h+='L '+str(Dx)+','+str(Dy)+' '
          Dx=Dx-dirxy[0]*(first+length/2)
          Dy=Dy-dirxy[1]*(first+length/2)
          h+='L '+str(Dx)+','+str(Dy)+' '
          Dx=Dx-dirxN*materialThickness
          Dy=Dy-diryN*materialThickness
          h+='L '+str(Dx)+','+str(Dy)+' '
          drawS(h)
      Vx=Vx+dirxy[0]*gapWidth+dirxN*firstVec+first*dirxy[0]
      Vy=Vy+dirxy[1]*gapWidth+diryN*firstVec+first*dirxy[1]
      s+='L '+str(Vx)+','+str(Vy)+' '
      Vx=Vx+dirxN*secondVec
      Vy=Vy+diryN*secondVec
      s+='L '+str(Vx)+','+str(Vy)+' '
    else:
      Vx=Vx+dirxy[0]*tabWidth+dirxN*firstVec
      Vy=Vy+dirxy[1]*tabWidth+diryN*firstVec
      s+='L '+str(Vx)+','+str(Vy)+' '
      Vx=Vx+dirxN*secondVec
      Vy=Vy+diryN*secondVec
      s+='L '+str(Vx)+','+str(Vy)+' '
    (secondVec,firstVec)=(-secondVec,-firstVec) # swap tab direction
    first=0
    
  #finish the line off
  s+='L '+str(rxy[0]+eoxy[0]*materialThickness+dirxy[0]*length)+','+str(rxy[1]+eoxy[1]*materialThickness+dirxy[1]*length)+' '
  if isTab and numDividers>0 and not isDivider: # draw last for divider joints in side walls
    for m in range(1,int(numDividers)+1):
      Dx=Vx
      Dy=Vy+dirxy[0]*divSpacing*m
      h='M '+str(Dx)+','+str(Dy)+' '
      Dx=rxy[0]+eoxy[0]*materialThickness+dirxy[0]*length
      Dy=Dy+dirxy[1]*tabWidth+diryN*firstVec+first*dirxy[1]
      h+='L '+str(Dx)+','+str(Dy)+' '
      Dx=Dx+dirxN*secondVec
      Dy=Dy+diryN*secondVec
      h+='L '+str(Dx)+','+str(Dy)+' '
      Dx=Vx
      Dy=Dy-(dirxy[1]*tabWidth+diryN*firstVec+first*dirxy[1])
      h+='L '+str(Dx)+','+str(Dy)+' '
      Dx=Dx-dirxN*secondVec
      Dy=Dy-diryN*secondVec
      h+='L '+str(Dx)+','+str(Dy)+' '
      drawS(h)
  return s

  
class BoxMaker(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options
      # Schroff only options
      self.arg_parser.add_argument('--schroff', action='store', type=int, dest='schroff', default=0, help='Enable Schroff mode')
      self.arg_parser.add_argument('--rail_height', action='store', type=float, dest='rail_height', default=10.0, help='Height of rail')
      self.arg_parser.add_argument('--rail_mount_depth', action='store', type=float, dest='rail_mount_depth', default=17.4, help='Depth at which to place hole for rail mount bolt')
      self.arg_parser.add_argument('--rail_mount_centre_offset', action='store', type=float, dest='rail_mount_centre_offset', default=0.0, help='How far toward row centreline to offset rail mount bolt (from rail centreline)')
      self.arg_parser.add_argument('--rows', action='store', type=int, dest='rows', default=0, help='Number of Schroff rows')
      self.arg_parser.add_argument('--hp', action='store', type=int, dest='hp', default=0, help='Width (TE/HP units) of Schroff rows')
      self.arg_parser.add_argument('--row_spacing', action='store', type=float, dest='row_spacing', default=10.0, help='Height of rail')

      # Normal tabbed boxed in the order they appear.
      self.arg_parser.add_argument('--container', type=str, dest='container', help='Container')
      self.arg_parser.add_argument('--unit', action='store', type=str, dest='unit', default='mm', help='Units of measure')
      self.arg_parser.add_argument('--length', action='store', type=float, dest='length', default=180, help='Length of Box')
      self.arg_parser.add_argument('--width', action='store', type=float, dest='width', default=240, help='Width of Box')
      self.arg_parser.add_argument('--depth', action='store', type=float, dest='height', default=50, help='Height of Box')
      self.arg_parser.add_argument('--tab', action='store', type=float, dest='tab', default=6.0 , help='Nominal Tab Width')
      self.arg_parser.add_argument('--equal', action='store', type=int, dest='equal', default=0, help='Equal/Prop Tabs')
      self.arg_parser.add_argument('--hairline', action='store', type=str, dest='hairline', default='1.0mm', help='Line Thickness')
      self.arg_parser.add_argument('--thickness', action='store', type=float, dest='thickness', default=3.0, help='Thickness of Material')
      self.arg_parser.add_argument('--kerf', action='store', type=float, dest='kerf', default=0.5, help='Kerf (width) of cut')
      self.arg_parser.add_argument('--clearance', action='store', type=float, dest='clearance', default=0.01, help='Clearance of joints')
      self.arg_parser.add_argument('--style', action='store', type=int, dest='style', default=1, help='Layout/Style')
      self.arg_parser.add_argument('--boxtype', action='store', type=int, dest='boxtype', default=1, help='Box type')
      self.arg_parser.add_argument('--div_l', action='store', type=int, dest='div_l', default=2, help='Dividers (Length axis)')
      self.arg_parser.add_argument('--div_w', action='store', type=int, dest='div_w', default=3, help='Dividers (Width axis)')
      self.arg_parser.add_argument('--keydiv', action='store', type=int, dest='keydiv', default=3, help='Key dividers into walls/floor')
      self.arg_parser.add_argument('--spacing', action='store', type=float, dest='spacing', default=25, help='Part Spacing')
      self.arg_parser.add_argument('--inside', action='store', type=inkex.Boolean, dest='inside', default=False, help='Are specified dimensions internal or external')

  def effect(self):
    global parent, nomTab, equalTabs, materialThickness, correction, divx, divy, hairline, linethickness, keydivwalls, keydivfloor, hp
    
    # Get access to main SVG document element and get its dimensions.
    svg = self.document.getroot()
    
    # Get the attributes:
    widthDoc  = self.svg.unittouu(svg.get('width'))
    heightDoc = self.svg.unittouu(svg.get('height'))

    # Create a new layer.
    layer = inkex.elements.etree.SubElement(svg, 'g')
    layer.set(inkex.addNS('label', 'inkscape'), 'newlayer')
    layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
    
    parent=self.svg.get_current_layer()
    
    # Get script's option values.
    hairline=self.options.hairline
    unit=self.options.unit
    inside=self.options.inside
    schroff=self.options.schroff

    # Set the line thickness
    linethickness=self.svg.unittouu(hairline)
    debug("Hairline %s linethickness %d " % (hairline, linethickness))
      
    if schroff:
        hp=self.options.hp
        rows=self.options.rows
        rail_height=self.svg.unittouu(str(self.options.rail_height)+unit)
        row_centre_spacing=self.svg.unittouu(str(122.5)+unit)
        row_spacing=self.svg.unittouu(str(self.options.row_spacing)+unit)
        rail_mount_depth=self.svg.unittouu(str(self.options.rail_mount_depth)+unit)
        rail_mount_centre_offset=self.svg.unittouu(str(self.options.rail_mount_centre_offset)+unit)
        rail_mount_radius=self.svg.unittouu(str(2.5)+unit)
    
    ## minimally different behaviour for schroffmaker.inx vs. boxmaker.inx
    ## essentially schroffmaker.inx is just an alternate interface with different
    ## default settings, some options removed, and a tiny amount of extra logic
    if schroff:
        ## schroffmaker.inx
        X = self.svg.unittouu(str(self.options.hp * 5.08) + unit)
        # 122.5mm vertical distance between mounting hole centres of 3U Schroff panels
        row_height = rows * (row_centre_spacing + rail_height)
        # rail spacing in between rows but never between rows and case panels
        row_spacing_total = (rows - 1) * row_spacing
        Y = row_height + row_spacing_total
    else:
        ## boxmaker.inx
        X = self.svg.unittouu( str(self.options.length)  + unit )
        Y = self.svg.unittouu( str(self.options.width) + unit )

    Z = self.svg.unittouu( str(self.options.height)  + unit )

    materialThickness = self.svg.unittouu( str(self.options.thickness)  + unit )
    nomTab = self.svg.unittouu( str(self.options.tab) + unit )
    equalTabs=self.options.equal
    kerf = self.svg.unittouu( str(self.options.kerf)  + unit )
    clearance = self.svg.unittouu( str(self.options.clearance)  + unit )
    layout=self.options.style
    spacing = self.svg.unittouu( str(self.options.spacing)  + unit )
    boxtype = self.options.boxtype
    divx = self.options.div_l
    divy = self.options.div_w
    keydivwalls = 0 if self.options.keydiv == 3 or self.options.keydiv == 1 else 1
    keydivfloor = 0 if self.options.keydiv == 3 or self.options.keydiv == 2 else 1
    divOffset = keydivwalls*materialThickness
        
    if inside:  # if inside dimension selected correct values to outside dimension
      X += materialThickness*2
      Y += materialThickness*2
      Z += materialThickness*2

    debug("Length (X) %d Width (Y) %d Height (Z) %d" % (X, Y, Z))
    debug("was inside %s" % (inside))

    correction=kerf-clearance
    # check input values mainly to avoid python errors
    # TODO restrict values to *correct* solutions
    # TODO restrict divisions to logical values
    error=0
    if min(X,Y,Z)==0:
      inkex.errormsg(localization._('Error: Dimensions must be non zero'))
      error=1
    if max(X,Y,Z)>max(widthDoc,heightDoc)*10: # crude test
      inkex.errormsg(localization._('Error: Dimensions Too Large'))
      error=1
    if min(X,Y,Z)<3*nomTab:
      inkex.errormsg(localization._('Error: Tab size too large'))
      error=1
    if nomTab<materialThickness:
      debug("Nomtab %d Material thickness %d" % (nomTab, materialThickness))
      inkex.errormsg(localization._('Error: Tab size too small '))
      error=1     
    if materialThickness==0:
      inkex.errormsg(localization._('Error: Thickness is zero'))
      error=1     
    if materialThickness>min(X,Y,Z)/3: # crude test
      inkex.errormsg(localization._('Error: Material too thick'))
      error=1     
    if correction>min(X,Y,Z)/3: # crude test
      inkex.errormsg(localization._('Error: Kerf/Clearence too large'))
      error=1     
    if spacing>max(X,Y,Z)*10: # crude test
      inkex.errormsg(localization._('Error: Spacing too large'))
      error=1     
    if spacing<kerf:
      inkex.errormsg(localization._('Error: Spacing too small'))
      error=1     

    if error: exit()
   
    # layout format:(rootx),(rooty),Xlength,Ylength,tabInfo,tabbed,pieceType
    # root= (spacing,X,Y,Z) * values in tuple
    # tabInfo= <abcd> 0=holes 1=tabs
    # tabbed= <abcd> 0=no tabs 1=tabs on this side
    # (sides: a=top, b=right, c=bottom, d=left)
    # pieceType: 1=XY, 2=XZ, 3=ZY
    # note first two pieces in each set are the X-divider template and Y-divider template respectively
    if boxtype==2: # One side open (X,Y)
      if   layout==1: # Diagramatic Layout
        pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1010,0b1101,2],
                [(1,0,0,0),(2,0,0,1),Z,Y,0b1111,0b1110,3],
                [(2,0,0,1),(2,0,0,1),X,Y,0b0000,0b1111,1],
                [(3,1,0,1),(2,0,0,1),Z,Y,0b1111,0b1011,3],
                [(2,0,0,1),(1,0,0,0),X,Z,0b1010,0b0111,2]]
      elif layout==2: # 3 Piece Layout
        pieces=[[(2,0,0,1),(2,0,1,0),X,Z,0b1010,0b1101,2],[(1,0,0,0),(1,0,0,0),Z,Y,0b1111,0b1110,3],
                [(2,0,0,1),(1,0,0,0),X,Y,0b0000,0b1111,1]]
      elif layout==3: # Inline(compact) Layout
        pieces=[[(5,2,0,2),(1,0,0,0),X,Z,0b1111,0b1101,2],[(3,2,0,0),(1,0,0,0),Z,Y,0b0101,0b1110,3],
                [(4,2,0,1),(1,0,0,0),Z,Y,0b0101,0b1011,3],[(2,1,0,0),(1,0,0,0),X,Y,0b0000,0b1111,1],
                [(6,3,0,2),(1,0,0,0),X,Z,0b1111,0b0111,2]]
      elif layout==4: # Diagramatic Layout with Alternate Tab Arrangement
        pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1001,0b1101,2],[(1,0,0,0),(2,0,0,1),Z,Y,0b1100,0b1110,3],
                [(2,0,0,1),(2,0,0,1),X,Y,0b1100,0b1111,1],[(3,1,0,1),(2,0,0,1),Z,Y,0b0110,0b1011,3],
                [(4,1,0,2),(2,0,0,1),X,Y,0b0110,0b0000,1],[(2,0,0,1),(1,0,0,0),X,Z,0b1100,0b0111,2]]
    elif boxtype==3: # Two sides open (X,Y and X,Z)
      if   layout==1: # Diagramatic Layout
        pieces=[[(2,0,0,1),(1,0,0,0),X,Z,0b1010,0b0111,2],[(1,0,0,0),(2,0,0,1),Z,Y,0b1111,0b1100,3],                
                [(2,0,0,1),(2,0,0,1),X,Y,0b0010,0b1101,1],[(3,1,0,1),(2,0,0,1),Z,Y,0b1111,0b1001,3]]
      elif layout==2: # 3 Piece Layout
        pieces=[[(2,0,0,1),(1,0,0,0),X,Z,0b1010,0b0111,2],[(1,0,0,0),(2,0,0,1),Z,Y,0b1111,0b1100,3],
                [(2,0,0,1),(2,0,0,1),X,Y,0b0010,0b1101,1]]
      elif layout==3: # Inline(compact) Layout
        pieces=[[(2,2,0,2),(1,0,0,0),X,Z,0b1010,0b0111,2],[(3,2,0,0),(1,0,0,0),Z,Y,0b1111,0b1100,3],
                [(2,1,0,0),(1,0,0,0),X,Y,0b0010,0b1101,1],[(4,2,0,1),(1,0,0,0),Z,Y,0b1111,0b1001,3]]
      elif layout==4: # Diagramatic Layout with Alternate Tab Arrangement
        pieces=[[(2,0,0,1),(1,0,0,0),X,Z,0b1100,0b0111,2],[(1,0,0,0),(2,0,0,1),Z,Y,0b1111,0b1100,3],
                [(2,0,0,1),(2,0,0,1),X,Y,0b1110,0b1101,1],[(3,1,0,1),(2,0,0,1),Z,Y,0b0110,0b1001,3]]
    elif boxtype==4: # Three sides open (X,Y, X,Z and Z,Y)
      if layout==2: # 3 Piece Layout
        pieces=[[(2,2,0,0),(2,0,1,0),X,Z,0b1111,0b1001,2],[(1,0,0,0),(1,0,0,0),Z,Y,0b1111,0b0110,3],
                [(2,2,0,0),(1,0,0,0),X,Y,0b1100,0b0011,1]]
      else:
        pieces=[[(3,3,0,0),(1,0,0,0),X,Z,0b1110,0b1001,2],[(1,0,0,0),(1,0,0,0),Z,Y,0b1111,0b0110,3],
                [(2,2,0,0),(1,0,0,0),X,Y,0b1100,0b0011,1]]
    elif boxtype==5: # Opposite ends open (X,Y)
      if   layout==1: # Diagramatic Layout
        pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1010,0b0101,2],[(3,1,0,1),(2,0,0,1),Z,Y,0b1111,0b1010,3],
                [(2,0,0,1),(1,0,0,0),X,Z,0b1010,0b0101,2],[(1,0,0,0),(2,0,0,1),Z,Y,0b1111,0b1010,3]]
      elif layout==2: # 2 Piece Layout
        pieces=[[(1,0,0,1),(1,0,1,1),X,Z,0b1010,0b0101,2],[(2,1,0,1),(1,0,0,1),Z,Y,0b1111,0b1010,3]]
      elif layout==3: # Inline(compact) Layout
        pieces=[[(1,0,0,0),(1,0,0,0),X,Z,0b1010,0b0101,2],[(3,2,0,0),(1,0,0,0),Z,Y,0b1111,0b1010,3],
                [(2,1,0,0),(1,0,0,0),X,Z,0b1010,0b0101,2],[(4,2,0,1),(2,0,0,0),Z,Y,0b1111,0b1010,3]]
      elif layout==4: # Diagramatic Layout with Alternate Tab Arrangement
        pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1011,0b0101,2],[(3,1,0,1),(2,0,0,1),Z,Y,0b0111,0b1010,3],
                [(2,0,0,1),(1,0,0,0),X,Z,0b1110,0b0101,2],[(1,0,0,0),(2,0,0,1),Z,Y,0b1101,0b1010,3]]
    elif boxtype==6: # 2 panels jointed (X,Y and Z,Y joined along Y)
      pieces=[[(1,0,0,0),(1,0,0,0),X,Y,0b1011,0b0100,1],[(2,1,0,0),(1,0,0,0),Z,Y,0b1111,0b0001,3]]
    else: # Fully enclosed
      if   layout==1: # Diagramatic Layout
        pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1010,0b1111,2],[(1,0,0,0),(2,0,0,1),Z,Y,0b1111,0b1111,3],
                [(2,0,0,1),(2,0,0,1),X,Y,0b0000,0b1111,1],[(3,1,0,1),(2,0,0,1),Z,Y,0b1111,0b1111,3],
                [(4,1,0,2),(2,0,0,1),X,Y,0b0000,0b1111,1],[(2,0,0,1),(1,0,0,0),X,Z,0b1010,0b1111,2]]
      elif layout==2: # 3 Piece Layout
        pieces=[[(2,0,0,1),(2,0,1,0),X,Z,0b1010,0b1111,2],[(1,0,0,0),(1,0,0,0),Z,Y,0b1111,0b1111,3],
                [(2,0,0,1),(1,0,0,0),X,Y,0b0000,0b1111,1]]
      elif layout==3: # Inline(compact) Layout
        pieces=[[(5,2,0,2),(1,0,0,0),X,Z,0b1111,0b1111,2],[(3,2,0,0),(1,0,0,0),Z,Y,0b0101,0b1111,3],
                [(6,3,0,2),(1,0,0,0),X,Z,0b1111,0b1111,2],[(4,2,0,1),(1,0,0,0),Z,Y,0b0101,0b1111,3],
                [(2,1,0,0),(1,0,0,0),X,Y,0b0000,0b1111,1],[(1,0,0,0),(1,0,0,0),X,Y,0b0000,0b1111,1]]
      elif layout==4: # Diagramatic Layout with Alternate Tab Arrangement
        pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1001,0b1111,2],[(1,0,0,0),(2,0,0,1),Z,Y,0b1100,0b1111,3],
                [(2,0,0,1),(2,0,0,1),X,Y,0b1100,0b1111,1],[(3,1,0,1),(2,0,0,1),Z,Y,0b0110,0b1111,3],
                [(4,1,0,2),(2,0,0,1),X,Y,0b0110,0b1111,1],[(2,0,0,1),(1,0,0,0),X,Z,0b1100,0b1111,2]]

    for idx, piece in enumerate(pieces): # generate and draw each piece of the box
      (xs,xx,xy,xz)=piece[0]
      (ys,yx,yy,yz)=piece[1]
      x=xs*spacing+xx*X+xy*Y+xz*Z  # root x co-ord for piece
      y=ys*spacing+yx*X+yy*Y+yz*Z  # root y co-ord for piece
      dx=piece[2]
      dy=piece[3]

      tabs=piece[4]
      a=tabs>>3&1; b=tabs>>2&1; c=tabs>>1&1; d=tabs&1 # extract tab status for each side

      tabbed=piece[5]
      atabs=tabbed>>3&1; btabs=tabbed>>2&1; ctabs=tabbed>>1&1; dtabs=tabbed&1 # extract tabbed flag for each side

      xspacing=(X-materialThickness)/(divy+1)
      yspacing=(Y-materialThickness)/(divx+1)
      xholes = 1 if piece[6]<3 else 0
      yholes = 1 if piece[6]!=2 else 0
      wall = 1 if piece[6]>1 else 0
      floor = 1 if piece[6]==1 else 0
      railholes = 1 if piece[6]==3 else 0

      if schroff and railholes:
        log("rail holes enabled on piece %d at (%d, %d)" % (idx, x+materialThickness,y+materialThickness))
        log("abcd = (%d,%d,%d,%d)" % (a,b,c,d))
        log("dxdy = (%d,%d)" % (dx,dy))
        rhxoffset = rail_mount_depth + materialThickness
        if idx == 1:
          rhx=x+rhxoffset
        elif idx == 3:
          rhx=x-rhxoffset+dx
        else:
          rhx=0
        log("rhxoffset = %d, rhx= %d" % (rhxoffset, rhx))
        rystart=y+(rail_height/2)+materialThickness
        if rows == 1:
          log("just one row this time, rystart = %d" % rystart)
          rh1y=rystart+rail_mount_centre_offset
          rh2y=rh1y+(row_centre_spacing-rail_mount_centre_offset)
          drawCircle(rail_mount_radius, (rhx, rh1y))
          drawCircle(rail_mount_radius, (rhx, rh2y))
        else:
          for n in range(0,rows):
            log("drawing row %d, rystart = %d" % (n+1, rystart))
            # if holes are offset (eg. Vector T-strut rails), they should be offset
            # toward each other, ie. toward the centreline of the Schroff row
            rh1y=rystart+rail_mount_centre_offset
            rh2y=rh1y+row_centre_spacing-rail_mount_centre_offset
            drawCircle(rail_mount_radius, (rhx, rh1y))
            drawCircle(rail_mount_radius, (rhx, rh2y))
            rystart+=row_centre_spacing+row_spacing+rail_height



      # generate and draw the sides of each piece
      drawS(side((x,y),(d,a),(-b,a),atabs * (-materialThickness if a else materialThickness),dx,(1,0),a,0,(keydivfloor|wall) * (keydivwalls|floor) * divx*yholes*atabs,yspacing,divOffset))          # side a
      drawS(side((x+dx,y),(-b,a),(-b,-c),btabs * (materialThickness if b else -materialThickness),dy,(0,1),b,0,(keydivfloor|wall) * (keydivwalls|floor) * divy*xholes*btabs,xspacing,divOffset))     # side b
      if atabs:
        drawS(side((x+dx,y+dy),(-b,-c),(d,-c),ctabs * (materialThickness if c else -materialThickness),dx,(-1,0),c,0,0,0,divOffset)) # side c
      else:
        drawS(side((x+dx,y+dy),(-b,-c),(d,-c),ctabs * (materialThickness if c else -materialThickness),dx,(-1,0),c,0,(keydivfloor|wall) * (keydivwalls|floor) * divx*yholes*ctabs,yspacing,divOffset)) # side c
      if btabs:
        drawS(side((x,y+dy),(d,-c),(d,a),dtabs * (-materialThickness if d else materialThickness),dy,(0,-1),d,0,0,0,divOffset))      # side d
      else:
        drawS(side((x,y+dy),(d,-c),(d,a),dtabs * (-materialThickness if d else materialThickness),dy,(0,-1),d,0,(keydivfloor|wall) * (keydivwalls|floor) * divy*xholes*dtabs,xspacing,divOffset))      # side d

      if idx==0:
        if not keydivwalls:
          a = 1
          b = 1
          c = 1
          d = 1
          atabs = 0
          btabs = 0
          ctabs = 0
          dtabs = 0
        y=4*spacing+1*Y+2*Z  # root y co-ord for piece 
        for n in range(0,divx): # generate X dividers
          x=n*(spacing+X)  # root x co-ord for piece      
          drawS(side((x,y),(d,a),(-b,a),keydivfloor*atabs*(-materialThickness if a else materialThickness),dx,(1,0),a,1,0,0,divOffset))          # side a
          drawS(side((x+dx,y),(-b,a),(-b,-c),keydivwalls*btabs*(materialThickness if keydivwalls*b else -materialThickness),dy,(0,1),b,1,divy*xholes,xspacing,divOffset))     # side b
          drawS(side((x+dx,y+dy),(-b,-c),(d,-c),keydivfloor*ctabs*(materialThickness if c else -materialThickness),dx,(-1,0),c,1,0,0,divOffset)) # side c
          drawS(side((x,y+dy),(d,-c),(d,a),keydivwalls*dtabs*(-materialThickness if d else materialThickness),dy,(0,-1),d,1,0,0,divOffset))      # side d
      elif idx==1:
        y=5*spacing+1*Y+3*Z  # root y co-ord for piece 
        for n in range(0,divy): # generate Y dividers 
          x=n*(spacing+Z)  # root x co-ord for piece
          drawS(side((x,y),(d,a),(-b,a),keydivwalls*atabs*(-materialThickness if a else materialThickness),dx,(1,0),a,1,divx*yholes,yspacing,materialThickness))          # side a
          drawS(side((x+dx,y),(-b,a),(-b,-c),keydivfloor*btabs*(materialThickness if b else -materialThickness),dy,(0,1),b,1,0,0,materialThickness))     # side b
          drawS(side((x+dx,y+dy),(-b,-c),(d,-c),keydivwalls*ctabs*(materialThickness if c else -materialThickness),dx,(-1,0),c,1,0,0,materialThickness)) # side c
          drawS(side((x,y+dy),(d,-c),(d,a),keydivfloor*dtabs*(-materialThickness if d else materialThickness),dy,(0,-1),d,1,0,0,materialThickness))      # side d

# Create effect instance and apply it.
effect = BoxMaker()
effect.run()
