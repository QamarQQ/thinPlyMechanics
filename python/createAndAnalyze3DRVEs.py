#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
=====================================================================================

Copyright (c) 2016-2019 Université de Lorraine or Luleå tekniska universitet
Author: Luca Di Stasio <luca.distasio@gmail.com>
                       <luca.distasio@ingpec.eu>

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in
the documentation and/or other materials provided with the distribution
Neither the name of the Université de Lorraine or Luleå tekniska universitet
nor the names of its contributors may be used to endorse or promote products
derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

=====================================================================================

DESCRIPTION

Tested with Abaqus Python 2.6 (64-bit) distribution in Windows 7.

'''
import sys, os
import numpy as np
import math
import subprocess
from os.path import isfile, join, exists
from platform import platform,system
from shutil import copyfile
import sqlite3
import locale
import ast
from datetime import datetime
from time import strftime, sleep
import timeit
from abaqus import *
from abaqusConstants import *
import section
import regionToolset
import displayGroupMdbToolset as dgm
import part
import material
import assembly
import step
import interaction
import load
import mesh
import optimization
import job
import sketch
import visualization
import xyPlot
import displayGroupOdbToolset as dgo
import connectorBehavior
from odbAccess import *
from odbMaterial import *
from odbSection import *
#import __main__

#===============================================================================#
#===============================================================================#
#                              I/O functions
#===============================================================================#
#===============================================================================#

#===============================================================================#
#                                  SHELL
#===============================================================================#

def printHelp():
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('*****************************************************************************************************')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('                       CREATION AND ANALYSIS OF RVEs/RUCs WITH FEM IN ABAQUS')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('                                              by')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('                                    Luca Di Stasio, 2016-2019')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('*****************************************************************************************************')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('Program syntax:')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('abaqus cae noGUI=createAndAnalyzeRVEs.py -- -dir/-directory <input file directory> -data <RVE base data> -iterables <parameters for iterations> -plot <parameters for plotting> -debug')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('Mandatory arguments:')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('-dir/-directory <input file directory>                     ===> full/path/to/folder/without/closing/slash')
    print >> sys.__stdout__,('-data <RVE base data>                                      ===> full/path/to/file/without/closing/slash')
    print >> sys.__stdout__,('-iterables <parameters for iterations>                     ===> full/path/to/file/without/extension')
    print >> sys.__stdout__,('-plot <parameters for plotting>                            ===> full/path/to/file/without/extension')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('Optional arguments:')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,('-debug                                                     ===> debug mode active')
    print >> sys.__stdout__,(' ')
    print >> sys.__stdout__,(' ')
    sys.exit()

#===============================================================================#
#                                  DECK file
#===============================================================================#

def fillDataDictionary(dataDict,inputKeywords,inputValue):
    if len(inputKeywords)>1:
        branchDict = dataDict.setdefault(inputKeywords[0],{})
        fillDataDictionary(branchDict,inputKeywords[1:],inputValue)
    else:
        dataDict[inputKeywords[0]] = inputValue


#===============================================================================#
#                                    CSV files
#===============================================================================#

def createCSVfile(dir,filename,titleline=None):
    if len(filename.split('.'))<2:
        filename += '.csv'
    with open(join(dir,filename),'w') as csv:
        if titleline != None:
            csv.write(titleline.replace('\n','') + '\n')
        else:
            csv.write('# Automatically created on ' + datetime.now().strftime('%d/%m/%Y') + ' at' + datetime.now().strftime('%H:%M:%S') + '\n')

def appendCSVfile(dir,filename,data):
    # data is a list of lists
    # each list is written to a row
    # no check is made on data consistency
    if len(filename.split('.'))<2:
        filename += '.csv'
    with open(join(dir,filename),'a') as csv:
        for row in data:
            line = ''
            for v,value in enumerate(row):
                if v>0:
                    line += ', '
                line += str(value)
            csv.write(line + '\n')

#===============================================================================#
#                              ABAQUS input files
#===============================================================================#

def createABQinpfile(path):
    with open(path,'w') as fi:
        fi.write('** ABAQUS INPUT FILE' + '\n')
        fi.write('** Automatically created on ' + datetime.now().strftime('%d/%m/%Y') + ' at ' + datetime.now().strftime('%H:%M:%S') + '\n')
        fi.write('**' + '\n')
        fi.write('**==============================================================================' + '\n')
        fi.write('** Copyright (c) 2016-2018 Universite de Lorraine & Lulea tekniska universitet' + '\n')
        fi.write('** Author: Luca Di Stasio <luca.distasio@gmail.com>' + '\n')
        fi.write('**                        <luca.distasio@ingpec.eu>' + '\n')
        fi.write('**' + '\n')
        fi.write('** Redistribution and use in source and binary forms, with or without' + '\n')
        fi.write('** modification, are permitted provided that the following conditions are met:' + '\n')
        fi.write('**'  + '\n')
        fi.write('** Redistributions of source code must retain the above copyright' + '\n')
        fi.write('** notice, this list of conditions and the following disclaimer.' + '\n')
        fi.write('** Redistributions in binary form must reproduce the above copyright' + '\n')
        fi.write('** notice, this list of conditions and the following disclaimer in' + '\n')
        fi.write('** the documentation and/or other materials provided with the distribution' + '\n')
        fi.write('** Neither the name of the Universite de Lorraine or Lulea tekniska universitet' + '\n')
        fi.write('** nor the names of its contributors may be used to endorse or promote products' + '\n')
        fi.write('** derived from this software without specific prior written permission.' + '\n')
        fi.write('**'  + '\n')
        fi.write('** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"' + '\n')
        fi.write('** AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE' + '\n')
        fi.write('** IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE' + '\n')
        fi.write('** ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE' + '\n')
        fi.write('** LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR' + '\n')
        fi.write('** CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF' + '\n')
        fi.write('** SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS' + '\n')
        fi.write('** INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN' + '\n')
        fi.write('** CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)' + '\n')
        fi.write('** ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE' + '\n')
        fi.write('** POSSIBILITY OF SUCH DAMAGE.' + '\n')
        fi.write('**==============================================================================' + '\n')
        fi.write('**' + '\n')

def readNodesFromInpFile(inpfullpath,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading content of original input file ...',True)
    with open(inpfullpath,'r') as inp:
        inpfilelines = inp.readlines()
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading nodes and saving to dictionary ...',True)
    allnodes = {}
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            allnodes[int(line.replace('\n','').split(',')[0])] = [float(line.replace('\n','').split(',')[1]),float(line.replace('\n','').split(',')[2])]
            #writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Stored node ' + str(int(line.replace('\n','').split(',')[0])) + ' with coordinates (' + str(float(line.replace('\n','').split(',')[1])) + ', ' + str(float(line.replace('\n','').split(',')[2])) + ')',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Node section ends at line ' + str(l),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'No more to go',True)
            store = False
            break
        elif store == True:
            allnodes[int(line.replace('\n','').split(',')[0])] = [float(line.replace('\n','').split(',')[1]),float(line.replace('\n','').split(',')[2])]
            #writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Stored node ' + str(int(line.replace('\n','').split(',')[0])) + ' with coordinates (' + str(float(line.replace('\n','').split(',')[1])) + ', ' + str(float(line.replace('\n','').split(',')[2])) + ')',True)
        elif ('*Node' in line or '*NODE' in line) and len(inpfilelines[l+1].replace('\n','').split(','))==3:
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Node section starts at line ' + str(l),True)
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    return allnodes

def readQuadsFromInpFile(inpfullpath,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading content of original input file ...',True)
    with open(inpfullpath,'r') as inp:
        inpfilelines = inp.readlines()
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading quadrilateral elements and saving to dictionary ...',True)
    allquads = {}
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            quadIndex = int(line.replace('\n','').split(',')[0])
            allquads[quadIndex] = []
            for node in line.replace('\n','').split(',')[1:]:
                allquads[quadIndex].append(int(node))
            store = False
            break
        elif store == True:
            quadIndex = int(line.replace('\n','').split(',')[0])
            allquads[quadIndex] = []
            for node in line.replace('\n','').split(',')[1:]:
                allquads[quadIndex].append(int(node))
        elif ('*Element, type=CPE8' in line or '*ELEMENT, type=CPE8' in line or '*Element, type=CPE4' in line or '*ELEMENT, type=CPE4' in line) and (len(inpfilelines[l+1].replace('\n','').split(','))==5 or len(inpfilelines[l+1].replace('\n','').split(','))==9):
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Quadrilateral elements section starts at line ' + str(l),True)
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    return allquads

def readNodesetFromInpFile(inpfullpath,name,expLength,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading content of original input file ...',True)
    with open(inpfullpath,'r') as inp:
        inpfilelines = inp.readlines()
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    if expLength>1:
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading node set ' + name + ' and saving to list ...',True)
        nodeset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        nodeset.append(int(index))
                store = False
                break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        nodeset.append(int(index))
            elif ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in [name.lower(),name.upper()]:
                store = True
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading node set ' + name + ' and saving to variable ...',True)
        for l,line in enumerate(inpfilelines):
            if ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in [name.lower(),name.upper()]:
                nodeset = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                break
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    return nodeset

def readElementsetFromInpFile(inpfullpath,name,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading content of original input file ...',True)
    with open(inpfullpath,'r') as inp:
        inpfilelines = inp.readlines()
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading element set ' + name + ' and saving to list ...',True)
    elementset = []
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    elementset.append(int(index))
            store = False
            break
        elif store == True:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    elementset.append(int(index))
        elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in [name.lower(),name.upper()]:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    return elementset

def readNodesFromNodesInpFile(inpfullpath,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading nodes from included input file ...',True)
    with open(inpfullpath,'r') as inp:
        inpfilelines = inp.readlines()
    allnodes = {}
    for line in inpfilelines[1:]:
        allnodes[int(line.replace('\n','').split(',')[0])] = [float(line.replace('\n','').split(',')[1]),float(line.replace('\n','').split(',')[2])]
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    return allnodes

def writeNodesToNodesInpFile(inpfullpath,allnodes,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Writing nodes to included input file ...',True)
    with open(inpfullpath,'w') as inp:
        inp.write('*NODE' + '\n')
        for key in allnodes.keys():
            inp.write(' ' + str(key) + ', ' + str(allnodes[key][0]) + ', ' + str(allnodes[key][1]) + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

def readQuadsFromQuadsInpFile(inpfullpath,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Reading quads from included input file ...',True)
    with open(inpfullpath,'r') as inp:
        inpfilelines = inp.readlines()
    allquads = {}
    for line in inpfilelines:
        id = int(line.replace('\n','').split(',')[0])
        nodes = line.replace('\n','').split(',')[1:]
        nodesId = []
        for node in nodes:
            nodesId.append(int(node))
        allquads[id] = nodesId
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    return allquads

def writeQuadsToQuadsInpFile(inpfullpath,allquads,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Writing quads to included input file ...',True)
    with open(inpfullpath,'w') as inp:
        inp.write('*ELEMENT, TYPE=CPE' + str(int(len(allquads[allquads.keys()[0]]))) + '\n')
        for key in allquads.keys():
            line = ' ' + str(key)
            for node in allquads[key]:
                line += ', ' + str(node)
            inp.write(line + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

#===============================================================================#
#                                 Log files
#===============================================================================#

def writeLineToLogFile(logFileFullPath,mode,line,toScreen):
    with open(logFileFullPath,mode) as log:
        log.write(line + '\n')
    if toScreen:
        print >> sys.__stdout__,(line + '\n')

def skipLineToLogFile(logFileFullPath,mode,toScreen):
    with open(logFileFullPath,mode) as log:
        log.write('\n')
    if toScreen:
        print >> sys.__stdout__,('\n')

def writeTitleSepLineToLogFile(logFileFullPath,mode,toScreen):
    with open(logFileFullPath,mode) as log:
        log.write('===============================================================================================\n')
    if toScreen:
        print >> sys.__stdout__,('===============================================================================================\n')

def writeTitleSecToLogFile(logFileFullPath,mode,title,toScreen):
    writeTitleSepLineToLogFile(logFileFullPath,mode,toScreen)
    writeTitleSepLineToLogFile(logFileFullPath,'a',toScreen)
    skipLineToLogFile(logFileFullPath,'a',toScreen)
    writeLineToLogFile(logFileFullPath,'a',title,toScreen)
    skipLineToLogFile(logFileFullPath,'a',toScreen)
    writeLineToLogFile(logFileFullPath,'a','Starting on ' + datetime.now().strftime('%Y-%m-%d') + ' at ' + datetime.now().strftime('%H:%M:%S'),toScreen)
    skipLineToLogFile(logFileFullPath,'a',toScreen)
    writeLineToLogFile(logFileFullPath,'a','Platform: ' + platform(),toScreen)
    skipLineToLogFile(logFileFullPath,'a',toScreen)
    writeTitleSepLineToLogFile(logFileFullPath,'a',toScreen)
    writeTitleSepLineToLogFile(logFileFullPath,'a',toScreen)
    skipLineToLogFile(logFileFullPath,'a',toScreen)

def writeErrorToLogFile(logFileFullPath,mode,exc,err,toScreen):
    with open(logFileFullPath,mode) as log:
        log.write('!!! ----------------------------------------------------------------------------------------!!!\n')
        log.write('\n')
        log.write('                                     AN ERROR OCCURED\n')
        log.write('\n')
        log.write('                                -------------------------\n')
        log.write('\n')
        log.write(str(exc) + '\n')
        log.write(str(err) + '\n')
        log.write('\n')
        log.write('Terminating program\n')
        log.write('\n')
        log.write('!!! ----------------------------------------------------------------------------------------!!!\n')
        log.write('\n')
    if toScreen:
        print >> sys.__stdout__,('!!! ----------------------------------------------------------------------------------------!!!\n')
        print >> sys.__stdout__,('\n')
        print >> sys.__stdout__,('                                     AN ERROR OCCURED\n')
        print >> sys.__stdout__,('\n')
        print >> sys.__stdout__,('                                -------------------------\n')
        print >> sys.__stdout__,('\n')
        print >> sys.__stdout__,(str(exc) + '\n')
        print >> sys.__stdout__,(str(err) + '\n')
        print >> sys.__stdout__,('\n')
        print >> sys.__stdout__,('Terminating program\n')
        print >> sys.__stdout__,('\n')
        print>> sys.__stdout__, ('!!! ----------------------------------------------------------------------------------------!!!\n')
        print>> sys.__stdout__, ('\n')

#===============================================================================#
#                                 Latex files
#===============================================================================#

def createLatexFile(folder,filename,documentclass,options=''):
    if not exists(folder):
        makedirs(folder)
    with open(join(folder,filename + '.tex'),'w') as tex:
        if options!='':
            tex.write('\\documentclass[' + options + ']{' + documentclass + '}\n')
        else:
            tex.write('\\documentclass{' + documentclass + '}\n')
        tex.write('\n')

def writeLatexPackages(folder,filename,packages,options):
    with open(join(folder,filename + '.tex'),'a') as tex:
        tex.write('%----------------------------------------------------------------------------------------------%\n')
        tex.write('%                                 Packages and basic declarations\n')
        tex.write('%----------------------------------------------------------------------------------------------%\n')
        tex.write('\n')
        for i,package in enumerate(packages):
            if options[i]!='':
                tex.write('\\usepackage[' + options[i] + ']{' + package + '}\n')
            else:
                tex.write('\\usepackage{' + package + '}\n')
        tex.write('\n')

def writeLatexDocumentStarts(folder,filename):
    with open(join(folder,filename + '.tex'),'a') as tex:
        tex.write('\n')
        tex.write('%----------------------------------------------------------------------------------------------%\n')
        tex.write('%----------------------------------------------------------------------------------------------%\n')
        tex.write('%                                            DOCUMENT STARTS\n')
        tex.write('%----------------------------------------------------------------------------------------------%\n')
        tex.write('%----------------------------------------------------------------------------------------------%\n')
        tex.write('\n')
        tex.write('\\begin{document}\n')
        tex.write('\n')

def writeLatexDocumentEnds(folder,filename):
    with open(join(folder,filename + '.tex'),'a') as tex:
        tex.write('\n')
        tex.write('\\end{document}\n')
        tex.write('\n')
        tex.write('%----------------------------------------------------------------------------------------------%\n')
        tex.write('%----------------------------------------------------------------------------------------------%\n')
        tex.write('%                                            DOCUMENT ENDS\n')
        tex.write('%----------------------------------------------------------------------------------------------%\n')
        tex.write('%----------------------------------------------------------------------------------------------%\n')
        tex.write('\n')

def writeLatexTikzPicStarts(folder,filename,options=''):
    with open(join(folder,filename + '.tex'),'a') as tex:
        tex.write('\n')
        tex.write('%Tikz picture starts%\n')
        tex.write('\n')
        if options!='':
            tex.write('\\begin{tikzpicture}[' + options + ']\n')
        else:
            tex.write('\\begin{tikzpicture}\n')

def writeLatexTikzPicEnds(folder,filename):
    with open(join(folder,filename + '.tex'),'a') as tex:
        tex.write('\n')
        tex.write('\\end{tikzpicture}\n')
        tex.write('%Tikz picture ends%\n')
        tex.write('\n')

def writeLatexTikzAxisStarts(folder,filename,options):
    with open(join(folder,filename + '.tex'),'a') as tex:
        tex.write('\n')
        tex.write('%Tikz axis starts%\n')
        tex.write('\n')
        if options!='':
            tex.write('\\begin{axis}[' + options + ']\n')
        else:
            tex.write('\\begin{axis}\n')

def writeLatexTikzAxisEnds(folder,filename):
    with open(join(folder,filename + '.tex'),'a') as tex:
        tex.write('\n')
        tex.write('\\end{axis}\n')
        tex.write('%Tikz axis ends%\n')
        tex.write('\n')

def writeLatexAddPlotTable(folder,filename,data,options):
    with open(join(folder,filename + '.tex'),'a') as tex:
        tex.write('\n')
        tex.write('\\addplot')
        if options!='':
            tex.write('[' + options + ']\n')
        tex.write('table{\n')
        for element in data:
            tex.write(str(element[0]) + ' ' + str(element[1]) + '\n')
        tex.write('};\n')

def writeLatexSinglePlot(folder,filename,data,axoptions,dataoptions,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: writeLatexSinglePlot(folder,filename,data,axoptions,dataoptions,logfilepath,baselogindent,logindent)',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create latex file',True)
    createLatexFile(folder,filename,'standalone')
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Write latex packages',True)
    writeLatexPackages(folder,filename,['inputenc','pgfplots','tikz'],['utf8','',''])
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Document starts',True)
    writeLatexDocumentStarts(folder,filename)
    writeLatexTikzPicStarts(folder,filename,'')
    writeLatexTikzAxisStarts(folder,filename,axoptions)
    writeLatexAddPlotTable(folder,filename,data,dataoptions)
    writeLatexTikzAxisEnds(folder,filename)
    writeLatexTikzPicEnds(folder,filename)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Document ends',True)
    writeLatexDocumentEnds(folder,filename)
    if 'Windows' in system():
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create Windows command file',True)
        cmdfile = join(folder,filename,'runlatex.cmd')
        with open(cmdfile,'w') as cmd:
            cmd.write('\n')
            cmd.write('CD ' + folder + '\n')
            cmd.write('\n')
            cmd.write('pdflatex ' + join(folder,filename.split('.')[0] + '.tex') + ' -job-name=' + filename.split('.')[0] + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Executing Windows command file...',True)
        try:
            subprocess.call('cmd.exe /C ' + cmdfile)
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
        except Exception:
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'ERROR',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + str(Exception),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + str(error),True)
            sys.exc_clear()
    elif 'Linux' in system():
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create Linux bash file',True)
        bashfile = join(folder,filename,'runlatex.sh')
        with open(bashfile,'w') as bsh:
            bsh.write('#!/bin/bash\n')
            bsh.write('\n')
            bsh.write('cd ' + folder + '\n')
            bsh.write('\n')
            bsh.write('pdflatex ' + join(folder,filename.split('.')[0] + '.tex') + ' -job-name=' + filename.split('.')[0] + '\n')
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Executing Linux bash file...',True)
            try:
                writeLineToLogFile(logfilename,'a',baselogindent + 3*logindent + 'Change permissions to ' + bashfile ,True)
                os.chmod(bashfile, 0o755)
                writeLineToLogFile(logfilename,'a','Run bash file',True)
                call('.' + bashfile)
                writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
            except Exception:
                writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'ERROR',True)
                writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + str(Exception),True)
                writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + str(error),True)
                sys.exc_clear()

def writeLatexMultiplePlots(folder,filename,data,axoptions,dataoptions,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: writeLatexMultiplePlots(folder,filename,data,axoptions,dataoptions,logfilepath,baselogindent,logindent)',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create latex file',True)
    createLatexFile(folder,filename,'standalone')
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Write latex packages',True)
    writeLatexPackages(folder,filename,['inputenc','pgfplots','tikz'],['utf8','',''])
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Document starts',True)
    writeLatexDocumentStarts(folder,filename)
    writeLatexTikzPicStarts(folder,filename,'')
    writeLatexTikzAxisStarts(folder,filename,axoptions)
    for k,datum in enumerate(data):
        writeLatexAddPlotTable(folder,filename,datum,dataoptions[k])
    writeLatexTikzAxisEnds(folder,filename)
    writeLatexTikzPicEnds(folder,filename)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Document ends',True)
    writeLatexDocumentEnds(folder,filename)
    if 'Windows' in system():
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create Windows command file',True)
        cmdfile = join(folder,'runlatex.cmd')
        with open(cmdfile,'w') as cmd:
            cmd.write('\n')
            cmd.write('CD ' + folder + '\n')
            cmd.write('\n')
            cmd.write('pdflatex ' + join(folder,filename.split('.')[0] + '.tex') + ' -job-name=' + filename.split('.')[0] + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Executing Windows command file...',True)
        try:
            subprocess.call('cmd.exe /C ' + cmdfile)
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
        except Exception,error:
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'ERROR',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + str(Exception),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + str(error),True)
            sys.exc_clear()
    elif 'Linux' in system():
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create Linux bash file',True)
        bashfile = join(folder,filename,'runlatex.sh')
        with open(bashfile,'w') as bsh:
            bsh.write('#!/bin/bash\n')
            bsh.write('\n')
            bsh.write('cd ' + folder + '\n')
            bsh.write('\n')
            bsh.write('pdflatex ' + join(folder,filename.split('.')[0] + '.tex') + ' -job-name=' + filename.split('.')[0] + '\n')
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Executing Linux bash file...',True)
            try:
                writeLineToLogFile(logfilename,'a',baselogindent + 3*logindent + 'Change permissions to ' + bashfile ,True)
                os.chmod(bashfile, 0o755)
                writeLineToLogFile(logfilename,'a','Run bash file',True)
                call('.' + bashfile)
                writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
            except Exception:
                writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'ERROR',True)
                writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + str(Exception),True)
                writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + str(error),True)
                sys.exc_clear()

def writeLatexGenericCommand(folder,filename,command,options,arguments):
    with open(join(folder,filename + '.tex'),'a') as tex:
        if options!='' and arguments!='':
            tex.write('\\'+ command +'[' + options + ']{' + arguments + '}\n')
        elif options!='':
            tex.write('\\'+ command +'{' + arguments + '}\n')
        else:
            tex.write('\\'+ command + '\n')
        tex.write('\n')

def writeLatexCustomLine(folder,filename,line):
    with open(join(folder,filename + '.tex'),'a') as tex:
        tex.write(line + '\n')

def writeLatexSetLength(folder,filename,length,value):
    with open(join(folder,filename + '.tex'),'a') as tex:
        tex.write('\\setlength' +'{' + '\\' + length + '}' +'{' + value + '}\n')

#===============================================================================#
#===============================================================================#
#                        General purpose functions
#===============================================================================#
#===============================================================================#

def rotateStress2D(sigXX,sigYY,tauXY,theta):
    sig11 = sigXX*np.cos(theta)*np.cos(theta)+sigYY*np.sin(theta)*np.sin(theta)+2*tauXY*np.sin(theta)*np.cos(theta)
    sig22 = sigXX*np.sin(theta)*np.sin(theta)+sigYY*np.cos(theta)*np.cos(theta)-2*tauXY*np.sin(theta)*np.cos(theta)
    tau12 = (sigYY-sigXX)*np.sin(theta)*np.cos(theta)+tauXY*(np.cos(theta)*np.cos(theta)-np.sin(theta)*np.sin(theta))
    return sig11,sig22,tau12

#===============================================================================#
#===============================================================================#
#                        Data extraction functions
#===============================================================================#
#===============================================================================#

def getPerfs(wd,sims,logfilepath,baselogindent,logindent):
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: getPerfs(wd,sims,logfilepath,baselogindent,logindent)',True)
    perf = []
    perf.append(['PROJECT NAME','DEBOND [°]','NUMBER OF CPUS [-]','USER TIME [s]','SYSTEM TIME [s]','USER TIME/TOTAL CPU TIME [%]','SYSTEM TIME/TOTAL CPU TIME [%]','TOTAL CPU TIME [s]','WALLCLOCK TIME [s]','WALLCLOCK TIME [m]','WALLCLOCK TIME [h]','WALLCLOCK TIME/TOTAL CPU TIME [%]','ESTIMATED FLOATING POINT OPERATIONS PER ITERATION [-]','MINIMUM REQUIRED MEMORY [MB]','MEMORY TO MINIMIZE I/O [MB]','TOTAL NUMBER OF ELEMENTS [-]','NUMBER OF ELEMENTS DEFINED BY THE USER [-]','NUMBER OF ELEMENTS DEFINED BY THE PROGRAM [-]','TOTAL NUMBER OF NODES [-]','NUMBER OF NODES DEFINED BY THE USER [-]','NUMBER OF NODES DEFINED BY THE PROGRAM [-]','TOTAL NUMBER OF VARIABLES [-]'])
    print('')
    for sim in sims:
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Extract performances for simulation ' + sim,True)
        usertime = 0
        systemtime = 0
        totalcpu = 0
        wallclock = 0
        floatops = 0
        minMemory = 0
        minIOmemory = 0
        totEl = 0
        userEl = 0
        progEl = 0
        totN = 0
        userN = 0
        progN = 0
        totVar = 0
        cpus = 0
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'In DAT file',True)
        if exists(join(wd,sim+'.dat')):
            with open(join(wd,sim+'.dat'),'r') as dat:
                lines = dat.readlines()
            for l,line in enumerate(lines):
                if 'JOB TIME SUMMARY' in line:
                    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  - JOB TIME SUMMARY',True)
                    for subline in lines[l:]:
                        if 'USER TIME' in subline:
                            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  - USER TIME',True)
                            usertime = float(subline.split('=')[1])
                        elif 'SYSTEM TIME' in subline:
                            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  - SYSTEM TIME',True)
                            systemtime = float(subline.split('=')[1])
                        elif 'TOTAL CPU TIME' in subline:
                            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  - TOTAL CPU TIME',True)
                            totalcpu = float(subline.split('=')[1])
                        elif 'WALLCLOCK TIME' in subline:
                            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  - WALLCLOCK TIME',True)
                            wallclock = float(subline.split('=')[1])
                elif 'M E M O R Y   E S T I M A T E' in line:
                    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  - MEMORY ESTIMATE',True)
                    values = lines[l+6].replace('\n','').split(' ')
                    while '' in values:
                        values.remove('')
                    floatops = float(values[1])
                    minMemory = float(values[2])
                    minIOmemory = float(values[3])
                elif 'P R O B L E M   S I Z E' in line:
                    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  - PROBLEM SIZE',True)
                    words = lines[l+3].replace('\n','').split(' ')
                    while '' in words:
                        words.remove('')
                    totEl = int(words[-1])
                    words = lines[l+4].split(' ')
                    while '' in words:
                        words.remove('')
                    userEl = int(words[-1])
                    words = lines[l+5].split(' ')
                    while '' in words:
                        words.remove('')
                    progEl = int(words[-1])
                    words = lines[l+6].split(' ')
                    while '' in words:
                        words.remove('')
                    totN = int(words[-1])
                    words = lines[l+7].split(' ')
                    while '' in words:
                        words.remove('')
                    userN = int(words[-1])
                    words = lines[l+8].split(' ')
                    while '' in words:
                        words.remove('')
                    progN = int(words[-1])
                    words = lines[l+9].split(' ')
                    while '' in words:
                        words.remove('')
                    totVar = int(words[-1])
        if exists(join(wd,sim+'.msg')):
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'In MSG file',True)
            with open(join(wd,sim+'.msg'),'r') as msg:
                lines = msg.readlines()
                for line in lines:
                    if 'USING THE DIRECT SOLVER WITH' in line:
                        words = line.replace('\n','').split(' ')
                        while '' in words:
                            words.remove('')
                        cpus = int(words[words.index('PROCESSORS')-1])
                writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  - PROCESSORS',True)
        perf.append([sim,cpus,usertime,systemtime,usertime/totalcpu,systemtime/totalcpu,totalcpu,wallclock,wallclock/60.,wallclock/3600.,wallclock/totalcpu,floatops,minMemory,minIOmemory,totEl,userEl,progEl,totN,userN,progN,totVar])
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Exiting function: getPerfs(wd,sims,logfilepath,baselogindent,logindent)',True)
    return perf

def getFrame(odbObj,step,frame):
    return odbObj.steps[odbObj.steps.keys()[step]].frames[frame]

def getFirstAndLastFrame(odbObj,step):
    return getFrame(odbObj,step,0),getFrame(odbObj,step,-1)

def getFirstAndLastFrameLastStep(odbObj):
    first, last = getFirstAndLastFrame(odbObj,-1)
    return first, last

def getSingleNodeSet(odbObj,part,nodeSet):
    if part==None:
        result = odbObj.rootAssembly.nodeSets[nodeSet]
    else:
        result = odbObj.rootAssembly.instances[part].nodeSets[nodeSet]
    return result

def getSingleElementSet(odbObj,part,elementSet):
    if part==None:
        result = odbObj.rootAssembly.elementSets[elementSet]
    else:
        result = odbObj.rootAssembly.instances[part].elementSets[elementSet]
    return result

def getSingleSetNodeCoordinates(odbObj,step,frame,part,nodeSet):
    frameObj = getFrame(odbObj,step,frame)
    allCoords = frameObj.fieldOutputs['COORD'].getSubset(position=NODAL)
    coords = allCoords.getSubset(region=odbObj.rootAssembly.instances[part].nodeSets[nodeSet])
    return coords

def getMultipleSetsNodeCoordinates(odbObj,nodeSets):
    coords = {}
    for set in nodeSets:
        step = set[0]
        frame = set[1]
        part = set[2]
        nodeSet = set[3]
        coords[nodeSet] = getSingleSetNodeCoordinates(odbObj,step,frame,part,nodeSet)
    return coords

def extractAndSaveNodesCoordinates(odbObj,nodeSetsData,folder,filename,ext):
    nodeSets = getMultipleSetsNodeCoordinates(odbObj,nodeSetsData)
    with open(join(folder,filename + ext),'w') as csv:
        if len(nodeSets[nodeSetsData[0][3]].values[0].data)==1:
            string = 'X'
        elif len(nodeSets[nodeSetsData[0][3]].values[0].data)==2:
            string = 'X, Y'
        elif len(nodeSets[nodeSetsData[0][3]].values[0].data)==3:
            string = 'X, Y, Z'
        csv.write('DATA\n')
        csv.write('NODE SET' + ', ' + 'NODE TYPE, NODE LABEL, ' + string + '\n')
        for set in nodeSetsData:
            for value in nodeSets[set[3]].values:
                line = ''
                line = set[3] + ', ' + 'NODAL' + ', ' + str(value.nodeLabel)
                for datum in value.data:
                    line += ', ' + str(datum)
                csv.write(line + '\n')

def getAllNodes(odbObj,step,frameN):
    allNodes = {}
    frame = getFrame(odbObj,step,frameN)
    nodesCoords = frame.fieldOutputs['COORD'].getSubset(position=NODAL)
    for value in nodesCoords.values:
        components = []
        for component in value.data:
            components.append(component)
        allNodes[str(value.nodeLabel)] = components
    return allNodes

def getAndSaveAllNodes(odbObj,step,frameN,folder,filename,ext):
    allNodes = {}
    frame = getFrame(odbObj,step,frameN)
    nodesCoords = frame.fieldOutputs['COORD'].getSubset(position=NODAL)
    for value in nodesCoords.values:
        components = []
        for component in value.data:
            components.append(component)
        allNodes[str(value.nodeLabel)] = components
    with open(join(folder,filename + ext),'w') as csv:
        if len(nodesCoords.values[0].data)==1:
            string = 'X'
        elif len(nodesCoords.values[0].data)==2:
            string = 'X, Y'
        elif len(nodesCoords.values[0].data)==3:
            string = 'X, Y, Z'
        csv.write('DATA\n')
        csv.write('NODE TYPE, NODE LABEL, ' + string + '\n')
        for value in nodesCoords.values:
            line = ''
            line = 'NODAL' + ', ' + str(value.nodeLabel)
            for datum in value.data:
                line += ', ' + str(datum)
            csv.write(line + '\n')
    return allNodes

def getAllIntPoints(odbObj,step,frameN):
    allIntPoints = {}
    frame = getFrame(odbObj,step,frameN)
    intpointCoords = frame.fieldOutputs['COORD'].getSubset(position=INTEGRATION_POINT)
    for value in intpointCoords.values:
        components = []
        for component in value.data:
            components.append(component)
        allIntPoints[str(value.elementLabel)+'-'+str(value.integrationPoint)] = components
    return allIntPoints

def getAndSaveAllIntPoints(odbObj,step,frameN,folder,filename,ext):
    allIntPoints = {}
    frame = getFrame(odbObj,step,frameN)
    intpointCoords = frame.fieldOutputs['COORD'].getSubset(position=INTEGRATION_POINT)
    for value in intpointCoords.values:
        components = []
        for component in value.data:
            components.append(component)
        allIntPoints[str(value.elementLabel)+'-'+str(value.integrationPoint)] = components
    with open(join(folder,filename + ext),'w') as csv:
        if len(intpointCoords.values[0].data)==1:
            string = 'X'
        elif len(intpointCoords.values[0].data)==2:
            string = 'X, Y'
        elif len(intpointCoords.values[0].data)==3:
            string = 'X, Y, Z'
        csv.write('DATA\n')
        csv.write('NODE TYPE, NODE LABEL, ' + string + '\n')
        for value in intpointCoords.values:
            line = ''
            line = 'INTEGRATION_POINT' + ', ' + str(value.elementLabel)+'-'+str(value.integrationPoint)
            for datum in value.data:
                line += ', ' + str(datum)
            csv.write(line + '\n')
    return allIntPoints

def getFieldOutput(odbObj,step,frame,fieldOutput,subset=None,pos=None):
    frame = getFrame(odbObj,step,frame)
    if subset!=None:
        if pos==1:
            out = frame.fieldOutputs[fieldOutput].getSubset(region=subset,position=INTEGRATION_POINT)
        elif pos==2:
            out = frame.fieldOutputs[fieldOutput].getSubset(region=subset,position=NODAL)
        elif pos==3:
            out = frame.fieldOutputs[fieldOutput].getSubset(region=subset,position=ELEMENT_NODAL)
        elif pos==4:
            out = frame.fieldOutputs[fieldOutput].getSubset(region=subset,position=CENTROID)
        else:
            out = frame.fieldOutputs[fieldOutput].getSubset(region=subset)
    else:
        out = frame.fieldOutputs[fieldOutput]
    return out

def extractAndSaveFieldOutput(odbObj,step,frameN,folder,filename,ext,fieldOutput,subset=None,pos=None):
    frame = getFrame(odbObj,step,frameN)
    nodes = getAllNodes(odbObj,step,frameN)
    intpoints = getAllIntPoints(odbObj,step,frameN)
    if subset!=None:
        if pos==1:
            out = frame.fieldOutputs[fieldOutput].getSubset(region=subset,position=INTEGRATION_POINT)
        elif pos==2:
            out = frame.fieldOutputs[fieldOutput].getSubset(region=subset,position=NODAL)
        elif pos==3:
            out = frame.fieldOutputs[fieldOutput].getSubset(region=subset,position=ELEMENT_NODAL)
        elif pos==4:
            out = frame.fieldOutputs[fieldOutput].getSubset(region=subset,position=CENTROID)
        else:
            out = frame.fieldOutputs[fieldOutput].getSubset(region=subset)
    else:
        out = frame.fieldOutputs[fieldOutput]
    with open(join(folder,filename + ext),'w') as csv:
        if fieldOutput== 'U' or fieldOutput=='RF':
            if len(out.values[0].data)==1:
                string = 'X, ' + fieldOutput + '1'
            elif len(out.values[0].data)==2:
                string = 'X, Y, '  + fieldOutput + '1' + ', ' + fieldOutput + '2'
            elif len(out.values[0].data)==3:
                string = 'X, Y, Z, '  + fieldOutput + '1' + ', ' + fieldOutput + '2' + ', ' + fieldOutput + '3'
        elif fieldOutput== 'S' or fieldOutput=='EE':
            if len(out.values[0].data)==2:
                string = 'X, ' + fieldOutput + '11' + ', '  + fieldOutput + '12'
            elif len(out.values[0].data)==4:
                string = 'X, Y, '  + fieldOutput + '11' + ', ' + fieldOutput + '22' + ', ' + fieldOutput + '33' + ', ' + fieldOutput + '12'
            elif len(out.values[0].data)==6:
                string = 'X, Y, Z, '  + fieldOutput + '11' + ', ' + fieldOutput + '22' + ', ' + fieldOutput + '33' + ', ' + fieldOutput + '12' + ', ' + fieldOutput + '13' + ', ' + fieldOutput + '23'
        csv.write('HEAT MAP\n')
        csv.write('NODE TYPE, NODE LABEL, ' + string + '\n')
        for value in out.values:
            if 'NODAL' in str(value.position):
                line = ''
                line = 'NODAL' + ', ' + str(value.nodeLabel)
                for datum in nodes[str(value.nodeLabel)]:
                    line += ', ' + str(datum)
                for datum in value.data:
                    line += ', ' + str(datum)
                csv.write(line + '\n')
            elif 'INTEGRATION_POINT' in str(value.position):
                line = ''
                line = 'INTEGRATION_POINT' + ', ' + str(value.elementLabel)+'-'+str(value.integrationPoint)
                for datum in intpoints[str(value.elementLabel)+'-'+str(value.integrationPoint)]:
                    line += ', ' + str(datum)
                for datum in value.data:
                    line += ', ' + str(datum)
                csv.write(line + '\n')

def getDispVsReactionOnBoundarySubset(odbObj,step,frame,part,subset,component):
    set = getSingleNodeSet(odbObj,part,subset)
    disp = getFieldOutput(odbObj,-1,-1,'U',set)
    countdisp = 0
    meandisp = 0
    for value in disp.values:
        countdisp += 1
        meandisp += value.data[component]
    meandisp /= countdisp
    force = getFieldOutput(odbObj,-1,-1,'RF',set)
    totalforce = 0
    for value in force.values:
        totalforce += value.data[component]
    return meandisp,totalforce

def getJintegrals(wd,sim,ncontours,stepN):
    with open(join(wd,sim + '.dat'),'r') as dat:
        lines = dat.readlines()
    for l,line in enumerate(lines):
        if 'S T E P       ' + str(stepN) + '     S T A T I C   A N A L Y S I S' in line:
            stepStart = l
    values = []
    for l,line in enumerate(lines):
        if 'J - I N T E G R A L   E S T I M A T E S' in line and l>stepStart:
            for n in range(1,int(np.ceil(ncontours/5))+1):
                if n>1:
                    temp = filter(lambda x: x!=' ' and x!='', lines[l+6+int(np.ceil(ncontours/5))+n].replace('\n','').split(' '))
                else:
                    temp = filter(lambda x: x!=' ' and x!='', lines[l+6+int(np.ceil(ncontours/5))+n].replace('\n','').split(' '))[2:]
                for value in temp:
                    values.append(float(value))
            break
    return values

#===============================================================================#
#===============================================================================#
#                        Data reporting functions
#===============================================================================#
#===============================================================================#

def writePerfToFile(od,outfile,performanceslist):
    with open(join(od,outfile),'w') as csv:
        for performances in performanceslist:
            line = ''
            for i,performance in enumerate(performances):
                if i>0:
                    line += ','
                line += str(performance)
            csv.write(line + '\n')

#===============================================================================#
#===============================================================================#
#                        Model creation functions
#===============================================================================#
#===============================================================================#

def reportSketchGeomElements(sketchGeometry,sketchVertices,logfilepath,baselogindent,logindent):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'The sketch has ' + str(len(sketchGeometry)) + ' geometric elements',True)
    for key in sketchGeometry.keys():
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'fiberGeometry[' + str(key) + '] = ' + str(sketchGeometry[key]),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'The sketch has ' + str(len(sketchVertices)) + ' vertices',True)
    for key in sketchVertices.keys():
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'fiberVertices[' + str(key) + '] = ' + str(sketchVertices[key]),True)

def defineSetOfVerticesByBoundingSphere(modelpart,Cx,Cy,Cz,R,setName,logfile,indent,toScreen):
    setOfVertices = modelpart.vertices.getByBoundingSphere(center=(Cx,Cy,Cz),radius=R)
    modelpart.Set(vertices=setOfVertices, name=setName)
    writeLineToLogFile(logfile,'a',indent + '-- ' + setName,toScreen)

def defineSetOfEdgesByClosestPoints(modelpart,Ax,Ay,Az,Bx,By,Bz,setName,logfile,indent,toScreen):
    setOfEdges = modelpart.edges.getClosest(coordinates=((Ax,Ay,Az),(Bx,By,Bz),))[0][0]
    modelpart.Set(edges = modelpart.edges[setOfEdges.index:setOfEdges.index+1], name=setName)
    writeLineToLogFile(logfile,'a',indent + '-- ' + setName,toScreen)

def defineSetOfFacesByFindAt(modelpart,Ax,Ay,Az,setName,logfile,indent,toScreen):
    setOfFaces = modelpart.faces.findAt(coordinates=(Ax,Ay,Az))
    modelpart.Set(faces = modelpart.faces[setOfFaces.index:setOfFaces.index+1], name=setName)
    writeLineToLogFile(logfile,'a',indent + '-- ' + setName,toScreen)

def create2Drectanglesketch(currentmodel,partName,partDimensionality,partType,sizeOfSheet,Ax,Ay,Bx,By,Cx,Cy,Dx,Dy,Clabel,Dlabel,logfilepath,baselogindent,logindent):
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: create2Drectanglesketch(currentmodel,partName,partDimensionality,partType,sizeOfSheet,Ax,Ay,Bx,By,Cx,Cy,Dx,Dy,Clabel,Dlabel,logfilepath,baselogindent,logindent)',True)
    # create sketch
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Initialize sketch to draw the external shape of the RVE ...',True)
    currentsketch = currentmodel.ConstrainedSketch(name='__profile__',sheetSize=sizeOfSheet)
    currentsketch.setPrimaryObject(option=STANDALONE)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # create rectangle
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw a rectangle ...',True)
    currentsketch.rectangle(point1=(Ax, Ay), point2=(Bx,By))
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # set dimension labels
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Set dimension labels ...',True)
    v = currentsketch.vertices
    currentsketch.ObliqueDimension(vertex1=v[0], vertex2=v[1], textPoint=(Cx,Cy), value=Clabel)
    currentsketch.ObliqueDimension(vertex1=v[1], vertex2=v[2], textPoint=(Dx,Dy), value=Dlabel)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # assign to part
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Assign sketch geometry to the part ...',True)
    currentpart = currentmodel.Part(name='RVE',dimensionality=TWO_D_PLANAR,type=DEFORMABLE_BODY)
    currentpart = currentmodel.parts['RVE']
    currentpart.BaseShell(sketch=RVEsketch)
    currentsketch.unsetPrimaryObject()
    del currentmodel.sketches['__profile__']
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

def create2DRVEregion(currentmodel,rvetype,L,logfilepath,baselogindent,logindent):
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: create2DRVEregion(currentmodel,type,L,logfilepath,baselogindent,logindent)',True)
    # initialize parameters
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Initialize parameters ...',True)
    if rvetype=='quarter':
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Model: quarter of RVE',True)
        sizeOfSheet = 2*L
        Ax = 0.0
        Ay = 0.0
        Bx = L
        By = L
        Cx = 0.5*L
        Cy = 1.1*L
        Dx = 1.1*L
        Dy = 0.5*L
        Clabel = L
        Dlabel = L
    elif rvetype=='half':
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Model: quarter of RVE',True)
        sizeOfSheet = 3*L
        Ax = -L
        Ay = 0.0
        Bx = L
        By = L
        Cx = 1.1*L
        Cy = 0.5*L
        Dx = 0.0
        Dy = 1.1*L
        Clabel = L
        Dlabel = 2*L
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Model: quarter of RVE',True)
        sizeOfSheet = 3*L
        Ax = -L
        Ay = -L
        Bx = L
        By = L
        Cx = -1.1*L
        Cy = 0.0
        Dx = 0.0
        Dy = 1.1*L
        Clabel = 2*L
        Dlabel = 2*L
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  sheet size = ' + str(sizeOfSheet),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Ax = ' + str(Ax),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Ay = ' + str(Ay),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Bx = ' + str(Bx),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  By = ' + str(By),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Cx = ' + str(Cx),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Cy = ' + str(Cy),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Dx = ' + str(Dx),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Dy = ' + str(Dy),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Clabel = ' + str(Clabel),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '  Dlabel = ' + str(Dlabel),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Calling function: create2Drectanglesketch(currentmodel,partName,partDimensionality,partType,sizeOfSheet,Ax,Ay,Bx,By,Cx,Cy,Dx,Dy,Clabel,Dlabel,logfilepath,baselogindent,logindent)',True)
    create2Drectanglesketch(currentmodel,'RVE',TWO_D_PLANAR,DEFORMABLE_BODY,sizeOfSheet,Ax,Ay,Bx,By,Cx,Cy,Dx,Dy,Clabel,Dlabel,logfilepath,baselogindent + 2*logindent,logindent)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Successfully returned from function: create2Drectanglesketch(currentmodel,partName,partDimensionality,partType,sizeOfSheet,Ax,Ay,Bx,By,Cx,Cy,Dx,Dy,Clabel,Dlabel,logfilepath,baselogindent,logindent)',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

def applyBC(currentmodel,bc,logfilepath,baselogindent,logindent):
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: applyBC(currentmodel,bc,logfilepath,baselogindent,logindent)',True)
    if bc['type'] in ['YSYMM','ysymm','Ysymm','ySymm']:
        model.YsymmBC(name=bc['name'], createStepName='Load-Step',
            region=model.rootAssembly.instances['RVE-assembly'].sets[bc['set']], localCsys=None)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

def applyLoad(currentmodel,parameters,load,logfilepath,baselogindent,logindent):
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: applyLoad(currentmodel,load,logfilepath,baselogindent,logindent)',True)
    if load['type'] in ['appliedstrain','appliedStrain','Applied Strain','applied strain']:
        if load['type'] in ['x','X','1']:
            model.DisplacementBC(name=load['name'],createStepName='Load-Step',region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], u1=load['value']*L, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',localCsys=None)
        elif load['type'] in ['y','Y','2']:
            model.DisplacementBC(name=load['name'],createStepName='Load-Step',region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], u2=load['value']*L, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',localCsys=None)
        elif load['type'] in ['z','Z','3']:
            model.DisplacementBC(name=load['name'],createStepName='Load-Step',region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], u3=load['value']*L, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',localCsys=None)
    elif load['type'] in ['applieddisplacement','appliedDisplacement','Applied Displacement','applied displacement']:
        if load['type'] in ['x','X','1']:
            model.DisplacementBC(name=load['name'],createStepName='Load-Step',region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], u1=load['value'], amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',localCsys=None)
        elif load['type'] in ['y','Y','2']:
            model.DisplacementBC(name=load['name'],createStepName='Load-Step',region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], u2=load['value'], amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',localCsys=None)
        elif load['type'] in ['z','Z','3']:
            model.DisplacementBC(name=load['name'],createStepName='Load-Step',region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], u3=load['value'], amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',localCsys=None)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

def assignMeshControls(thisModel,assemblyName,setName,elementShape,controls,logfile,indent,toScreen):
    thisModel.rootAssembly.setMeshControls(regions=(thisModel.rootAssembly.instances[assemblyName].sets[setName].faces), elemShape=elementShape, technique=controls)
    writeLineToLogFile(logfile,'a',indent + '-- ' + setName,toScreen)

def seedEdgeByNumber(thisModel,assemblyName,setName,seedsNumber,seedsConstraint,logfile,indent,toScreen):
    thisModel.rootAssembly.seedEdgeByNumber(edges=(thisModel.rootAssembly.instances[assemblyName].sets[setName].edges), number=int(seedsNumber), constraint=seedsConstraint)
    writeLineToLogFile(logfile,'a',indent + '-- ' + setName,toScreen)

def addVCCTnodesAtCrack(inpfullpath,parameters,nodes,quads,fNum,crNum,crack,lastNodeIndex,logfilepath,baselogindent,logindent):
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: addVCCTnodesAtCrackTip(parameters,lastNodeIndex,logfilepath,baselogindent,logindent)',True)
    skipLineToLogFile(logfilepath,'a',True)
    matrixCracktipIndex = lastNodeIndex + 1
    cracktipDummyIndex = lastNodeIndex + 2
    lastNodeIndex += 2
    if 'second' in parameters['mesh']['elements']['order']:
        matrixFbCracktipIndex = lastNodeIndex + 1
        fbCracktipDummyIndex = lastNodeIndex + 2
        lastNodeIndex += 2
    ctposIndex = readNodesetFromInpFile(inpfullpath,'FIBER'+str(fNum+1)+'-CRACK'+str(cNum+1)+'-CRACKTIPPOS',1,logfilepath,baselogindent + logindent,logindent)
    fiberBondedElset = readElementsetFromInpFile(inpfullpath,'FIBER'+str(fNum+1)+'-SECONDRING-CT1-FIRSTBOUNDED',logfilepath,baselogindent + logindent,logindent)
    fiberDebondedElset = readElementsetFromInpFile(inpfullpath,'FIBER'+str(fNum+1)+'-SECONDRING-CT1-CRACKREFINE',logfilepath,baselogindent + logindent,logindent)
    matrixBondedElset = readElementsetFromInpFile(inpfullpath,'FIBER'+str(fNum+1)+'-THIRDRING-CT1-FIRSTBOUNDED',logfilepath,baselogindent + logindent,logindent)
    matrixDebondedElset = readElementsetFromInpFile(inpfullpath,'FIBER'+str(fNum+1)+'-THIRDRING-CT1-CRACKREFINE',logfilepath,baselogindent + logindent,logindent)
    if not crack['isSymm']:
        ctnegIndex = readNodesetFromInpFile(inpfullpath,'FIBER'+str(f+1)+'-CRACK'+str(cNum+1)+'-CRACKTIPNEG',1,logfilepath,baselogindent + logindent,logindent)
        fiberBondedElset = readElementsetFromInpFile(inpfullpath,'FIBER'+str(fNum+1)+'-SECONDRING-CT2-FIRSTBOUNDED',logfilepath,baselogindent + logindent,logindent)
        fiberDebondedElset = readElementsetFromInpFile(inpfullpath,'FIBER'+str(fNum+1)+'-SECONDRING-CT2-CRACKREFINE',logfilepath,baselogindent + logindent,logindent)
        matrixBondedElset = readElementsetFromInpFile(inpfullpath,'FIBER'+str(fNum+1)+'-THIRDRING-CT2-FIRSTBOUNDED',logfilepath,baselogindent + logindent,logindent)
        matrixDebondedElset = readElementsetFromInpFile(inpfullpath,'FIBER'+str(fNum+1)+'-THIRDRING-CT2-CRACKREFINE',logfilepath,baselogindent + logindent,logindent)

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

def addVCCTnodes(parameters,nodesfullfile,quadsfullfile,lastNodeIndex,logfilepath,baselogindent,logindent):
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: addVCCTnodes(parameters,nodesfullfile,quadsfullfile,lastNodeIndex,logfilepath,baselogindent,logindent)',True)
    skipLineToLogFile(logfilepath,'a',True)
    nodes = readNodesFromNodesInpFile(nodesfullfile,logfilepath,baselogindent + logindent,logindent)
    quads = readQuadsFromQuadsInpFile(quadsfullfile,logfilepath,baselogindent + logindent,logindent)
    for f, fiber in enumerate(parameters['fibers'].values()):
        if fiber['isCracked']:
            for cNum,crackKey in enumerate(fiber['cracks'].keys()):
                crack = fiber['cracks'][crackKey]
                if crack['isMeasured'] and 'VCCT' in crack['measurement-methods']:
                    crackfacesNodeset = readNodesetFromInpFile(inpfullpath,'FIBER'+str(f+1)+'-CRACK'+str(cNum+1),1,logfilepath,baselogindent + logindent,logindent)

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

def addVCCTtoInputfile(parameters,mdbData,logfilepath,baselogindent,logindent):
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: addVCCTToInputfile(parameters,mdbData,logfilepath,baselogindent,logindent)',True)
    skipLineToLogFile(logfilepath,'a',True)
    # input file name and path
    inpname = mdbData['jobname'] + '.inp'
    inpfullpath = join(parameters['input']['wd'],inpname)
    # modified input file name
    modinpname = 'Job-VCCTandJintegral-' + parameters['input']['modelname'] + '.inp'
    nodesinpname = 'N-' + parameters['input']['modelname'].replace('-','') + '.inp'
    quadsinpname = 'Q-' + parameters['input']['modelname'].replace('-','') + '.inp'
    surfsetsinpname = 'S-' + parameters['input']['modelname'].replace('-','') + '.inp'
    modinpfullpath = join(parameters['input']['wd'],modinpname)
    nodesinpfullpath = join(parameters['input']['wd'],nodesinpname)
    quadsinpfullpath = join(parameters['input']['wd'],quadsinpname)
    surfsetsinpfullpath = join(parameters['input']['wd'],surfsetsinpname)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Working directory: ' + parameters['input']['wd'],True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Input file name: ' + inpname,True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Input file full path: ' + join(parameters['input']['wd'],inpname),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Modified input file name: ' + modinpname,True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Modified input file full path: ' + join(parameters['input']['wd'],modinpname),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Nodes input file name: ' + nodesinpname,True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Nodes input file full path: ' + join(parameters['input']['wd'],nodesinpname),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Quads input file name: ' + quadsinpname,True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Quads input file full path: ' + join(parameters['input']['wd'],quadsinpname),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Surface sets input file name: ' + surfsetsinpname,True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Surface sets input file full path: ' + join(parameters['input']['wd'],surfsetsinpname),True)
    createABQinpfile(modinpname)
    skipLineToLogFile(logfilepath,'a',True)
    numNodes = mdbData['numNodes']
    numEls = mdbData['numEls']
    numQuads = mdbData['numQuads']
    numTris = mdbData['numTris']
    lastNodeIndex = numNodes + 1000
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Total number of nodes = ' + str(numNodes),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Total number of elements = ' + str(numEls),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Total number of quadrilateral elements = ' + str(numQuads),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Total number of triangular elements = ' + str(numTris),True)
    skipLineToLogFile(logfilepath,'a',True)
    writeNodesToNodesInpFile(nodesinpfullpath,readNodesFromInpFile(inpfullpath,logfilepath,baselogindent + 2*logindent,logindent),logfilepath,baselogindent + logindent,logindent)
    writeQuadsToQuadsInpFile(quadsinpfullpath,readQuadsFromInpFile(inpfullpath,logfilepath,baselogindent + 2*logindent,logindent),logfilepath,baselogindent + logindent,logindent)
    northSideNodeset = readNodesetFromInpFile(inpfullpath,'UPPERSIDE',100,logfilepath,baselogindent + logindent,logindent)
    northeastIndex = readNodesetFromInpFile(inpfullpath,'NE-CORNER',1,logfilepath,baselogindent + logindent,logindent)
    northwestIndex = readNodesetFromInpFile(inpfullpath,'NW-CORNER',1,logfilepath,baselogindent + logindent,logindent)

def listGeomElements(logfilepath,baselogindent,logindent,fiberGeometry,fiberVertices):
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'The sketch has ' + str(len(fiberGeometry)) + ' geometric elements',True)
    for key in fiberGeometry.keys():
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'fiberGeometry[' + str(key) + '] = ' + str(fiberGeometry[key]),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'The sketch has ' + str(len(fiberVertices)) + ' vertices',True)
    for key in fiberVertices.keys():
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'fiberVertices[' + str(key) + '] = ' + str(fiberVertices[key]),True)

def createRVE(parameters,logfilepath,baselogindent,logindent):
    #===============================================================================#
    #                               Parameters
    #===============================================================================#
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: createRVE(parameters,logfilepath,logindent)',True)
    # assign most used parameters to variables
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Read and assign most used parameters to variables ...',True)
    baselogindent += logindent
    wd = parameters['input']['wd']
    caefilename = parameters['input']['caefilename'].split('.')[0] + '.cae'
    modelname = parameters['input']['modelname']
    L = parameters['geometry']['L']
    W = parameters['geometry']['W']
    Rf = parameters['geometry']['Rf']
    if 'full' in parameters['geometry']['fiber']['type']:
        CornerAy = -L
    elif 'half' in parameters['geometry']['fiber']['type']:
        CornerAy = 0.0
    elif 'quarter' in parameters['geometry']['fiber']['type']:
        CornerAy = 0.0
    else:
        CornerAy = 0.0
    if 'boundingPly' in parameters['BC']['northSide']['type'] and 'adjacentFibers' in parameters['BC']['northSide']['type']:
        nFibers = parameters['BC']['northSide']['nFibers']
        tRatio = parameters['BC']['northSide']['tRatio']
        Lply = nFibers*(2*L)
        Ludply = tRatio*(2*(L + Lply))
        CornerBy = L + Lply + Ludply
    elif 'boundingPly' in parameters['BC']['northSide']['type'] or 'adjacentFibers' in parameters['BC']['northSide']['type']:
        if 'adjacentFibers' in parameters['BC']['northSide']['type']:
            tRatio = parameters['BC']['northSide']['nFibers']
        else:
            tRatio = parameters['BC']['northSide']['tRatio']
        Lply = tRatio*(2*L)
        CornerBy = L + Lply
    else:
        CornerBy = L
    if 'boundingPly' in parameters['BC']['rightSide']['type'] and 'boundingPly' in parameters['BC']['leftSide']['type'] and 'adjacentFibers' in parameters['BC']['rightSide']['type'] and 'adjacentFibers' in parameters['BC']['leftSide']['type']:
        if 'quarter' in parameters['geometry']['fiber']['type']:
            skipLineToLogFile(logfilepath,'a',True)
            writeErrorToLogFile(logfilepath,'a','GEOMETRY','Clashing geometric requirements: asked for quarter fiber and for material on the left side. Review and select the appropriate.',True)
            sys.exit(2)
        wRatioRight = parameters['BC']['rightSide']['wRatio']
        wRatioLeft = parameters['BC']['leftSide']['wRatio']
        nFibersRight = parameters['BC']['rightSide']['nFibers']
        nFibersLeft = parameters['BC']['leftSide']['nFibers']
        wRightPly = nFibersRight*(2*L)
        wLeftPly = nFibersLeft*(2*L)
        wRightHPly = wRatioRight*(wRightPly+wLeftPly+2*L)
        wLeftHPly = wRatioLeft*(wRightPly+wLeftPly+2*L)
        CornerAx = -(L+wLeftPly+wLeftHPly)
        CornerBx = L+wRightPly+wRightHPly
    elif ('boundingPly' in parameters['BC']['rightSide']['type'] and 'boundingPly' in parameters['BC']['leftSide']['type']) or ('adjacentFibers' in parameters['BC']['rightSide']['type'] and 'adjacentFibers' in parameters['BC']['leftSide']['type']):
        if 'quarter' in parameters['geometry']['fiber']['type']:
            skipLineToLogFile(logfilepath,'a',True)
            writeErrorToLogFile(logfilepath,'a','GEOMETRY','Clashing geometric requirements: asked for quarter fiber and for material on the left side. Review and select the appropriate.',True)
            sys.exit(2)
        if 'boundingPly' in parameters['BC']['rightSide']['type'] and 'boundingPly' in parameters['BC']['leftSide']['type']:
            wRatioRight = parameters['BC']['rightSide']['wRatio']
            wRatioLeft = parameters['BC']['leftSide']['wRatio']
            wRightHPly = wRatioRight*(2*L)
            wLeftHPly = wRatioLeft*(2*L)
        else:
            wRatioRight = parameters['BC']['rightSide']['nFibers']
            wRatioLeft = parameters['BC']['leftSide']['nFibers']
        wRightPly = wRatioRight*(2*L)
        wLeftPly = wRatioLeft*(2*L)
        CornerAx = -(L+wLeftPly)
        CornerBx = L+wRightPly
    elif 'boundingPly' in parameters['BC']['rightSide']['type'] and 'adjacentFibers' in parameters['BC']['rightSide']['type']:
        wRatioRight = parameters['BC']['rightSide']['wRatio']
        nFibersRight = parameters['BC']['rightSide']['nFibers']
        wRightPly = nFibersRight*(2*L)
        wRightHPly = wRatioRight*(wRightPly+wLeftPly+2*L)
        CornerAx = -L
        CornerBx = L+wRightPly+wRightHPly
    elif 'boundingPly' in parameters['BC']['leftSide']['type'] and 'adjacentFibers' in parameters['BC']['leftSide']['type']:
        if 'quarter' in parameters['geometry']['fiber']['type']:
            skipLineToLogFile(logfilepath,'a',True)
            writeErrorToLogFile(logfilepath,'a','GEOMETRY','Clashing geometric requirements: asked for quarter fiber and for material on the left side. Review and select the appropriate.',True)
            sys.exit(2)
        wRatioLeft = parameters['BC']['leftSide']['wRatio']
        nFibersLeft = parameters['BC']['leftSide']['nFibers']
        wLeftPly = nFibersLeft*(2*L)
        wLeftHPly = wRatioLeft*(wRightPly+wLeftPly+2*L)
        CornerAx = -(L+wLeftPly+wLeftHPly)
        CornerBx = L
    elif 'boundingPly' in parameters['BC']['rightSide']['type'] or 'adjacentFibers' in parameters['BC']['rightSide']['type']:
        if 'boundingPly' in parameters['BC']['rightSide']['type']:
            wRatioRight = parameters['BC']['rightSide']['wRatio']
        else:
            wRatioRight = parameters['BC']['rightSide']['nFibers']
        wRatioRight = parameters['BC']['rightSide']['wRatio']
        wRightPly = wRatioRight*(2*L)
        CornerAx = -L
        CornerBx = L+wRightPly
    elif 'boundingPly' in parameters['BC']['leftSide']['type'] or 'adjacentFibers' in parameters['BC']['leftSide']['type']:
        if 'quarter' in parameters['geometry']['fiber']['type']:
            skipLineToLogFile(logfilepath,'a',True)
            writeErrorToLogFile(logfilepath,'a','GEOMETRY','Clashing geometric requirements: asked for quarter fiber and for material on the left side. Review and select the appropriate.',True)
            sys.exit(2)
        if 'boundingPly' in parameters['BC']['leftSide']['type']:
            wRatioLeft = parameters['BC']['leftSide']['wRatio']
        else:
            wRatioLeft = parameters['BC']['leftSide']['nFibers']
        wRatioLeft = parameters['BC']['leftSide']['wRatio']
        wLeftPly = wRatioLeft*(2*L)
        CornerAx = -(L+wLeftPly)
        CornerBx = L
    else:
        CornerBx = L
        if 'quarter' in parameters['geometry']['fiber']['type']:
            CornerAx = 0.0
        else:
            CornerAx = -L
    theta = parameters['geometry']['theta'] # in degrees !!!
    deltatheta = parameters['geometry']['deltatheta'] # in degrees !!!
    LD = parameters['geometry']['LD']['ratio']*W
    RD = parameters['geometry']['RD']['ratio']*np.min([Rf*deltatheta*np.pi/180.0,LD])
    if np.abs(theta)>0.0:
        if theta-deltatheta<=0.0:
            skipLineToLogFile(logfilepath,'a',True)
            writeErrorToLogFile(logfilepath,'a','GEOMETRY','The provided debond geometry is not correct: the debond ends at or under the symmetry line at 0 degree',True)
            sys.exit(2)
        elif theta+deltatheta>=180.0:
            skipLineToLogFile(logfilepath,'a',True)
            writeErrorToLogFile(logfilepath,'a','GEOMETRY','The provided debond geometry is not correct: the debond ends at or under the symmetry line at 180 degree',True)
            sys.exit(2)
    deltapsi = parameters['mesh']['size']['deltapsi'] # in degrees !!!
    deltaphi = parameters['mesh']['size']['deltaphi'] # in degrees !!!
    delta = parameters['mesh']['size']['delta'] # in degrees !!!
    minElNum = parameters['mesh']['elements']['minElNum']
    if ((theta+deltatheta-deltapsi)<=0.0 or (theta+deltatheta-deltapsi)/delta<minElNum) and ((theta+deltatheta+deltapsi+deltaphi)>=180.0 or (180.0-(theta+deltatheta+deltapsi+deltaphi))/delta<minElNum):
        deltapsi = 0.6*((180.0-(theta+deltatheta))-np.max([0.5*(theta+deltatheta),0.1*(180.0-(theta+deltatheta)),minElNum*delta]))
        deltaphi = 0.4*((180.0-(theta+deltatheta))-np.max([0.5*(theta+deltatheta),0.1*(180.0-(theta+deltatheta)),minElNum*delta]))
    elif (theta+deltatheta-deltapsi)<=0.0 or (theta+deltatheta-deltapsi)/delta<minElNum:
        deltapsi = (theta+deltatheta) - np.max([0.5*(theta+deltatheta),minElNum*delta])
    elif (theta+deltatheta+deltapsi+deltaphi)>=180.0 or (180.0-(theta+deltatheta+deltapsi+deltaphi))/delta<minElNum:
        deltapsi = 0.6*((180.0-(theta+deltatheta))-np.max([0.1*(180.0-(theta+deltatheta)),minElNum*delta]))
        deltaphi = 0.4*((180.0-(theta+deltatheta))-np.max([0.1*(180.0-(theta+deltatheta)),minElNum*delta]))
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Working directory: ' + wd,True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'CAE database name: ' + caefilename,True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Model name: ' + modelname,True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'L: ' + str(L),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Rf: ' + str(Rf),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'L/Rf: ' + str(L/Rf),True)
    if 'boundingPly' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Lply: ' + str(Lply),True)
    if 'boundingPly' in parameters['BC']['rightSide']['type'] and 'boundingPly' in parameters['BC']['leftSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'wRightPly: ' + str(wRightPly),True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'wLeftPly: ' + str(wLeftPly),True)
    elif 'boundingPly' in parameters['BC']['rightSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'wRightPly: ' + str(wRightPly),True)
    elif 'boundingPly' in parameters['BC']['leftSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'wLeftPly: ' + str(wLeftPly),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'theta: ' + str(theta),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'deltatheta: ' + str(deltatheta),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'deltapsi: ' + str(deltapsi),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'deltaphi: ' + str(deltaphi),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'delta: ' + str(delta),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'minElnum: ' + str(minElNum),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    #===============================================================================#
    #                          Model database creation
    #===============================================================================#
    # if CAE database exists, open it; otherwise create new one
    caefullpath = join(wd,caefilename)
    if isfile(caefullpath):
        skipLineToLogFile(logfilepath,'a',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'CAE database already exists. Opening it ...',True)
        openMdb(caefullpath)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    else:
        skipLineToLogFile(logfilepath,'a',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'CAE database does not exist. Creating it ...',True)
        mdb.saveAs(caefullpath)
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    # create and assign model object to variable for lighter code
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Creating model ' + modelname + ' ...',True)
    mdb.Model(name=modelname)
    model = mdb.models[modelname]
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)
    #===============================================================================#
    #                             Parts creation
    #===============================================================================#
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Creating part ...',True)
    # create sketch
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Initialize sketch to draw the external shape of the RVE ...',True)
    RVEsketch = model.ConstrainedSketch(name='__profile__',
        sheetSize=3*L)
    RVEsketch.setPrimaryObject(option=STANDALONE)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # create rectangle
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw a rectangle ...',True)
    RVEsketch.rectangle(point1=(CornerAx,CornerAy), point2=(CornerBx,CornerBy))
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # set dimension labels
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Set dimension labels ...',True)
    v = RVEsketch.vertices
    RVEsketch.ObliqueDimension(vertex1=v[0], vertex2=v[1], textPoint=(1.1*CornerAx,0.5*CornerBy), value=CornerBy)
    RVEsketch.ObliqueDimension(vertex1=v[1], vertex2=v[2], textPoint=(0.0,1.1*CornerBy), value=(-CornerAx+CornerBx))
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # assign to part
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Assign sketch geometry to the part ...',True)
    RVEpart = model.Part(name='RVE',dimensionality=TWO_D_PLANAR,type=DEFORMABLE_BODY)
    RVEpart = model.parts['RVE']
    RVEpart.BaseShell(sketch=RVEsketch)
    RVEsketch.unsetPrimaryObject()
    del model.sketches['__profile__']
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # create reference to geometrical objects (faces, edges and vertices) of the part
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create reference to geometrical objects of the part ...',True)
    RVEfaces = RVEpart.faces
    RVEedges = RVEpart.edges
    RVEvertices = RVEpart.vertices
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # create geometrical transform to draw partition sketch
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create geometrical transform to draw partition sketch ...',True)
    transformToSketch = RVEpart.MakeSketchTransform(sketchPlane=RVEfaces[0], sketchPlaneSide=SIDE1, origin=(0.0,0.0,0.0))
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # create sketch
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create sketch ...',True)
    fiberSketch = model.ConstrainedSketch(name='fiberSketch',sheetSize=3*L, gridSpacing=L/100.0, transform=transformToSketch)
    fiberSketch = model.sketches['fiberSketch']
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # create reference to geometrical objects (faces, edges and vertices) of the partition sketch
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create reference to geometrical objects of the partition sketch ...',True)
    fiberGeometry = fiberSketch.geometry
    fiberVertices = fiberSketch.vertices
    fiberSketch.setPrimaryObject(option=SUPERIMPOSE)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # Project reference onto sketch
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Project reference onto sketch ...',True)
    RVEpart.projectReferencesOntoSketch(sketch=fiberSketch, filter=COPLANAR_EDGES)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # draw fiber and circular sections for mesh generation
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw fiber and circular sections for mesh generation ...',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Fiber',True)
    if 'full' in parameters['geometry']['fiber']['type']:
        fiberSketch.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(-Rf, 0.0))
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 0.75*Rf',True)
        fiberSketch.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(-0.75*Rf, 0.0)) # fiberGeometry[7]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 0.5*Rf',True)
        fiberSketch.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(-0.5*Rf, 0.0)) # fiberGeometry[8]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.25*Rf',True)
        if L>2*Rf:
            fiberSketch.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(-1.25*Rf, 0.0)) # fiberGeometry[9]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.5*Rf',True)
            fiberSketch.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(-1.5*Rf, 0.0)) # fiberGeometry[10]
        else:
            fiberSketch.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(-(Rf+0.25*(L-Rf)), 0.0)) # fiberGeometry[9]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.5*Rf',True)
            fiberSketch.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(-(Rf+0.5*(L-Rf)), 0.0)) # fiberGeometry[10]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    elif 'half' in parameters['geometry']['fiber']['type']:
        fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-Rf, 0.0), point2=(Rf,0.0), direction=CLOCKWISE) # fiberGeometry[6]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 0.75*Rf',True)
        fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-0.75*Rf, 0.0), point2=(0.75*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[7]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 0.5*Rf',True)
        fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-0.5*Rf, 0.0), point2=(0.5*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[8]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.25*Rf',True)
        if L>2*Rf:
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-1.25*Rf, 0.0), point2=(1.25*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[9]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.5*Rf',True)
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-1.5*Rf, 0.0), point2=(1.5*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[10]
        else:
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-(Rf+0.25*(L-Rf)), 0.0), point2=((Rf+0.25*(L-Rf)),0.0), direction=CLOCKWISE) # fiberGeometry[9]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.5*Rf',True)
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-(Rf+0.5*(L-Rf)), 0.0), point2=((Rf+0.5*(L-Rf)),0.0), direction=CLOCKWISE) # fiberGeometry[10]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    elif 'quarter' in parameters['geometry']['fiber']['type']:
        fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, 0.0+Rf), point2=(Rf,0.0), direction=CLOCKWISE) # fiberGeometry[6]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 0.75*Rf',True)
        fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, 0.0+0.75*Rf), point2=(0.75*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[7]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 0.5*Rf',True)
        fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, 0.0+0.5*Rf), point2=(0.5*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[8]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.25*Rf',True)
        if L>2*Rf:
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, 0.0+1.25*Rf), point2=(1.25*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[9]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.5*Rf',True)
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, 0.0+1.5*Rf), point2=(1.5*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[10]
        else:
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, 0.0+(Rf+0.25*(L-Rf))), point2=((Rf+0.25*(L-Rf)),0.0), direction=CLOCKWISE) # fiberGeometry[9]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.5*Rf',True)
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, 0.0+(Rf+0.5*(L-Rf))), point2=((Rf+0.5*(L-Rf)),0.0), direction=CLOCKWISE) # fiberGeometry[10]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    else:
        fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-Rf, 0.0), point2=(Rf,0.0), direction=CLOCKWISE) # fiberGeometry[6]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 0.75*Rf',True)
        fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-0.75*Rf, 0.0), point2=(0.75*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[7]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 0.5*Rf',True)
        fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-0.5*Rf, 0.0), point2=(0.5*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[8]
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.25*Rf',True)
        if L>2*Rf:
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-1.25*Rf, 0.0), point2=(1.25*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[9]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.5*Rf',True)
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-1.5*Rf, 0.0), point2=(1.5*Rf,0.0), direction=CLOCKWISE) # fiberGeometry[10]
        else:
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-(Rf+0.25*(L-Rf)), 0.0), point2=((Rf+0.25*(L-Rf)),0.0), direction=CLOCKWISE) # fiberGeometry[9]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Arc at 1.5*Rf',True)
            fiberSketch.ArcByCenterEnds(center=(0.0, 0.0), point1=(-(Rf+0.5*(L-Rf)), 0.0), point2=((Rf+0.5*(L-Rf)),0.0), direction=CLOCKWISE) # fiberGeometry[10]
            listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # calculate angles for construction lines
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Calculate angles for construction lines ...',True)
    alpha = theta + deltatheta - deltapsi
    beta = theta + deltatheta + deltapsi
    gamma = theta + deltatheta + deltapsi + deltaphi
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # draw construction lines
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw construction lines ...',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Construction line at ' + str(theta+deltatheta) + ' deg',True)
    fiberSketch.ConstructionLine(point1=(0.0, 0.0), angle=(theta+deltatheta)) # fiberGeometry[11]
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[6], entity2=fiberGeometry[11],addUndoState=False)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Construction line at ' + str(alpha) + ' deg',True)
    fiberSketch.ConstructionLine(point1=(0.0, 0.0), angle=alpha) # fiberGeometry[12]
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[6], entity2=fiberGeometry[12],addUndoState=False)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Construction line at ' + str(beta) + ' deg',True)
    fiberSketch.ConstructionLine(point1=(0.0, 0.0), angle=beta) # fiberGeometry[13]
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[6], entity2=fiberGeometry[13],addUndoState=False)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Construction line at ' + str(gamma) + ' deg',True)
    fiberSketch.ConstructionLine(point1=(0.0, 0.0), angle=gamma) # fiberGeometry[14]
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[6], entity2=fiberGeometry[14],addUndoState=False)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # draw angular sections to identify the crack and for mesh generation
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'draw angular sections to identify the crack and for mesh generation ...',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute internal and external radii ...',True)
    Rint = 0.75*Rf
    if L>2*Rf:
        Rext = 1.25*Rf
    else:
        Rext = Rf+0.25*(L-Rf)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create first circular section ...',True)
    Ax = Rint*np.cos(alpha*np.pi/180.0)
    Ay = 0.0+Rint*np.sin(alpha*np.pi/180.0)
    Bx = Rext*np.cos(alpha*np.pi/180.0)
    By = 0.0+Rext*np.sin(alpha*np.pi/180.0)
    fiberSketch.Line(point1=(Ax,Ay),point2=(Bx,By)) # fiberGeometry[15]
    fiberSketch.PerpendicularConstraint(entity1=fiberGeometry[7], entity2=fiberGeometry[15],addUndoState=False)
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[15], entity2=fiberGeometry[7],addUndoState=False)
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[16], entity2=fiberGeometry[9],addUndoState=False)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create second circular section ...',True)
    Ax = Rint*np.cos((theta+deltatheta)*np.pi/180.0)
    Ay = 0.0+Rint*np.sin((theta+deltatheta)*np.pi/180.0)
    Bx = Rext*np.cos((theta+deltatheta)*np.pi/180.0)
    By = 0.0+Rext*np.sin((theta+deltatheta)*np.pi/180.0)
    fiberSketch.Line(point1=(Ax,Ay),point2=(Bx,By)) # fiberGeometry[16]
    fiberSketch.PerpendicularConstraint(entity1=fiberGeometry[7], entity2=fiberGeometry[16],addUndoState=False)
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[17], entity2=fiberGeometry[7],addUndoState=False)
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[18], entity2=fiberGeometry[9],addUndoState=False)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create third circular section ...',True)
    Ax = Rint*np.cos(beta*np.pi/180.0)
    Ay = 0.0+Rint*np.sin(beta*np.pi/180.0)
    Bx = Rext*np.cos(beta*np.pi/180.0)
    By = 0.0+Rext*np.sin(beta*np.pi/180.0)
    fiberSketch.Line(point1=(Ax,Ay),point2=(Bx,By)) # fiberGeometry[17]
    fiberSketch.PerpendicularConstraint(entity1=fiberGeometry[7], entity2=fiberGeometry[17],addUndoState=False)
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[19], entity2=fiberGeometry[7],addUndoState=False)
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[20], entity2=fiberGeometry[9],addUndoState=False)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    #raw_input()
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create fourth circular section ...',True)
    Ax = Rint*np.cos(gamma*np.pi/180.0)
    Ay = 0.0+Rint*np.sin(gamma*np.pi/180.0)
    Bx = Rext*np.cos(gamma*np.pi/180.0)
    By = 0.0+Rext*np.sin(gamma*np.pi/180.0)
    fiberSketch.Line(point1=(Ax,Ay),point2=(Bx,By)) # fiberGeometry[18]
    fiberSketch.PerpendicularConstraint(entity1=fiberGeometry[7], entity2=fiberGeometry[18],addUndoState=False)
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[21], entity2=fiberGeometry[7],addUndoState=False)
    fiberSketch.CoincidentConstraint(entity1=fiberVertices[22], entity2=fiberGeometry[9],addUndoState=False)
    listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # if theta != 0, construct second crack tip
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Construct second crack tip ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Calculate angles for construction lines ...',True)
        alpha = theta - deltatheta + deltapsi
        beta = theta - deltatheta - deltapsi
        gamma = theta - deltatheta - deltapsi - deltaphi
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        #raw_input()
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
        # draw construction lines
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw construction lines ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Construction line at ' + str(theta+deltatheta) + ' deg',True)
        fiberSketch.ConstructionLine(point1=(0.0, 0.0), angle=(theta-deltatheta)) # fiberGeometry[19]
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[6], entity2=fiberGeometry[19],addUndoState=False)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        #raw_input()
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Construction line at ' + str(alpha) + ' deg',True)
        fiberSketch.ConstructionLine(point1=(0.0, 0.0), angle=alpha) # fiberGeometry[20]
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[6], entity2=fiberGeometry[20],addUndoState=False)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        #raw_input()
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Construction line at ' + str(beta) + ' deg',True)
        fiberSketch.ConstructionLine(point1=(0.0, 0.0), angle=beta) # fiberGeometry[21]
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[6], entity2=fiberGeometry[21],addUndoState=False)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        #raw_input()
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Construction line at ' + str(gamma) + ' deg',True)
        fiberSketch.ConstructionLine(point1=(0.0, 0.0), angle=gamma) # fiberGeometry[22]
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[6], entity2=fiberGeometry[22],addUndoState=False)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        #raw_input()
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
        # draw angular sections to identify the crack and for mesh generation
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'draw angular sections to identify the crack and for mesh generation ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute internal and external radii ...',True)
        Rint = 0.75*Rf
        if L>2*Rf:
            Rext = 1.25*Rf
        else:
            Rext = Rf+0.25*(L-Rf)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        #raw_input()
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create first circular section ...',True)
        Ax = Rint*np.cos(alpha*np.pi/180.0)
        Ay = 0.0+Rint*np.sin(alpha*np.pi/180.0)
        Bx = Rext*np.cos(alpha*np.pi/180.0)
        By = 0.0+Rext*np.sin(alpha*np.pi/180.0)
        fiberSketch.Line(point1=(Ax,Ay),point2=(Bx,By)) # fiberGeometry[23]
        fiberSketch.PerpendicularConstraint(entity1=fiberGeometry[7], entity2=fiberGeometry[23],addUndoState=False)
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[-2], entity2=fiberGeometry[7],addUndoState=False)
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[-1], entity2=fiberGeometry[9],addUndoState=False)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        #raw_input()
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create second circular section ...',True)
        Ax = Rint*np.cos((theta+deltatheta)*np.pi/180.0)
        Ay = 0.0+Rint*np.sin((theta+deltatheta)*np.pi/180.0)
        Bx = Rext*np.cos((theta+deltatheta)*np.pi/180.0)
        By = 0.0+Rext*np.sin((theta+deltatheta)*np.pi/180.0)
        fiberSketch.Line(point1=(Ax,Ay),point2=(Bx,By)) # fiberGeometry[24]
        fiberSketch.PerpendicularConstraint(entity1=fiberGeometry[7], entity2=fiberGeometry[24],addUndoState=False)
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[-2], entity2=fiberGeometry[7],addUndoState=False)
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[-1], entity2=fiberGeometry[9],addUndoState=False)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        #raw_input()
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create third circular section ...',True)
        Ax = Rint*np.cos(beta*np.pi/180.0)
        Ay = 0.0+Rint*np.sin(beta*np.pi/180.0)
        Bx = Rext*np.cos(beta*np.pi/180.0)
        By = 0.0+Rext*np.sin(beta*np.pi/180.0)
        fiberSketch.Line(point1=(Ax,Ay),point2=(Bx,By)) # fiberGeometry[25]
        fiberSketch.PerpendicularConstraint(entity1=fiberGeometry[7], entity2=fiberGeometry[25],addUndoState=False)
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[-2], entity2=fiberGeometry[7],addUndoState=False)
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[-1], entity2=fiberGeometry[9],addUndoState=False)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        #raw_input()
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create fourth circular section ...',True)
        Ax = Rint*np.cos(gamma*np.pi/180.0)
        Ay = 0.0+Rint*np.sin(gamma*np.pi/180.0)
        Bx = Rext*np.cos(gamma*np.pi/180.0)
        By = 0.0+Rext*np.sin(gamma*np.pi/180.0)
        fiberSketch.Line(point1=(Ax,Ay),point2=(Bx,By)) # fiberGeometry[26]
        fiberSketch.PerpendicularConstraint(entity1=fiberGeometry[7], entity2=fiberGeometry[26],addUndoState=False)
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[-2], entity2=fiberGeometry[7],addUndoState=False)
        fiberSketch.CoincidentConstraint(entity1=fiberVertices[-1], entity2=fiberGeometry[9],addUndoState=False)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    # if bounding ply is present, draw interface line
    if 'boundingPly' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw upper ply interface line ...',True)
        if 'adjacentFibers' in parameters['BC']['northSide']['type']:
            fiberSketch.Line(point1=(CornerAx,L+Lply),point2=(CornerBx,L+Lply))
        else:
            fiberSketch.Line(point1=(CornerAx,L),point2=(CornerBx,L))
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if 'boundingPly' in parameters['BC']['rightSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw ply right interface line ...',True)
        if 'adjacentFibers' in parameters['BC']['northSide']['type']:
            fiberSketch.Line(point1=(CornerBx-wRightHPly,0.0),point2=(CornerBx-wRightHPly,L+Lply))
        else:
            fiberSketch.Line(point1=(CornerBx-wRightHPly,0.0),point2=(CornerBx-wRightHPly,L))
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if 'boundingPly' in parameters['BC']['leftSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw ply left interface line ...',True)
        if 'adjacentFibers' in parameters['BC']['northSide']['type']:
            fiberSketch.Line(point1=(CornerAx+wLeftHPly,0.0),point2=(CornerAx+wLeftHPly,L+Lply))
        else:
            fiberSketch.Line(point1=(CornerAx+wLeftHPly,0.0),point2=(CornerAx+wLeftHPly,L))
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if 'adjacentFibers' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw fibers above ...',True)
        for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
            fiberSketch.CircleByCenterPerimeter(center=(0.0, 0.0+(nFiber+1)*2*L), point1=(Rf, 0.0+(nFiber+1)*2*L))
        if 'adjacentFibers' in parameters['BC']['rightSide']['type']:
            for mFiber in range(0,parameters['BC']['rightSide']['nFibers']):
                for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
                    fiberSketch.CircleByCenterPerimeter(center=((mFiber+1)*2*L, 0.0+(nFiber+1)*2*L), point1=((mFiber+1)*2*L+Rf, 0.0+(nFiber+1)*2*L))
        if 'adjacentFibers' in parameters['BC']['leftSide']['type']:
            for mFiber in range(0,parameters['BC']['leftSide']['nFibers']):
                for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
                    fiberSketch.CircleByCenterPerimeter(center=(-(mFiber+1)*2*L, 0.0+(nFiber+1)*2*L), point1=(-(mFiber+1)*2*L+Rf, 0.0+(nFiber+1)*2*L))
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if 'adjacentFibers' in parameters['BC']['rightSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw fibers to the right ...',True)
        if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
            for nFiber in range(0,parameters['BC']['rightSide']['nFibers']):
                fiberSketch.CircleByCenterPerimeter(center=((nFiber+1)*2*L, 0.0), point1=((nFiber+1)*2*L-Rf, 0.0))
        else:
            for nFiber in range(0,parameters['BC']['rightSide']['nFibers']):
                fiberSketch.ArcByCenterEnds(center=((nFiber+1)*2*L, 0.0), point1=((nFiber+1)*2*L-Rf, 0.0), point2=((nFiber+1)*2*L+Rf,0.0), direction=CLOCKWISE)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if 'adjacentFibers' in parameters['BC']['leftSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Draw fibers to the left ...',True)
        if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
            for nFiber in range(0,parameters['BC']['leftSide']['nFibers']):
                fiberSketch.CircleByCenterPerimeter(center=(-(nFiber+1)*2*L, 0.0), point1=(-(nFiber+1)*2*L-Rf, 0.0))
        else:
            for nFiber in range(0,parameters['BC']['leftSide']['nFibers']):
                fiberSketch.ArcByCenterEnds(center=(-(nFiber+1)*2*L, 0.0), point1=(-(nFiber+1)*2*L-Rf, 0.0), point2=(-(nFiber+1)*2*L+Rf,0.0), direction=CLOCKWISE)
        listGeomElements(logfilepath,baselogindent+2*logindent,logindent,fiberGeometry,fiberVertices)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Assign partition sketch to part ...',True)
    pickedFaces = RVEfaces.findAt(coordinates=(0.0, 0.5*L, 0))
    RVEpart.PartitionFaceBySketch(faces=pickedFaces, sketch=fiberSketch)
    fiberSketch.unsetPrimaryObject()
    del model.sketches['fiberSketch']
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    mdb.save()

    #-------------------#
    #                   #
    #    create sets    #
    #                   #
    #-------------------#

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create sets ...',True)

    # create reference to geometric elements for lighter code
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create reference to geometric elements of the part ...',True)
    RVEvertices = RVEpart.vertices
    RVEedges = RVEpart.edges
    RVEfaces = RVEpart.faces
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'The part has ' + str(len(RVEvertices)) + ' vertices',True)
    for e,element in enumerate(RVEvertices):
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'RVEvertices[' + str(e) + '] = ' + str(element),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'The part has ' + str(len(RVEedges)) + ' edges',True)
    for e,element in enumerate(RVEedges):
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'RVEedges[' + str(e) + '] = ' + str(element),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'The part has ' + str(len(RVEfaces)) + ' faces',True)
    for e,element in enumerate(RVEfaces):
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'RVEfaces[' + str(e) + '] = ' + str(element),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    # sets of vertices
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Sets of vertices',True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        defineSetOfVerticesByBoundingSphere(RVEpart,Rf*np.cos((theta+deltatheta)*np.pi/180),Rf*np.sin((theta+deltatheta)*np.pi/180),0.0,0.0001*Rf,'CRACKTIPUP',logfilepath,baselogindent + 4*logindent,True)
        defineSetOfVerticesByBoundingSphere(RVEpart,Rf*np.cos((theta-deltatheta)*np.pi/180),Rf*np.sin((theta-deltatheta)*np.pi/180),0.0,0.0001*Rf,'CRACKTIPLOW',logfilepath,baselogindent + 4*logindent,True)
    else:
        defineSetOfVerticesByBoundingSphere(RVEpart,Rf*np.cos((theta+deltatheta)*np.pi/180),Rf*np.sin((theta+deltatheta)*np.pi/180),0.0,0.0001*Rf,'CRACKTIP',logfilepath,baselogindent + 4*logindent,True)

    defineSetOfVerticesByBoundingSphere(RVEpart,CornerBx,CornerBy,0.0,0.00001*Rf,'NE-CORNER',logfilepath,baselogindent + 4*logindent,True)
    defineSetOfVerticesByBoundingSphere(RVEpart,CornerAx,CornerBy,0.0,0.00001*Rf,'NW-CORNER',logfilepath,baselogindent + 4*logindent,True)
    defineSetOfVerticesByBoundingSphere(RVEpart,CornerBx,0.0,0.0,0.00001*Rf,'SE-CORNER',logfilepath,baselogindent + 4*logindent,True)
    defineSetOfVerticesByBoundingSphere(RVEpart,CornerAx,0.0,0.0,0.00001*Rf,'SW-CORNER',logfilepath,baselogindent + 4*logindent,True)

    if 'boundingPly' in parameters['BC']['northSide']['type']:
        if 'adjacentFibers' in parameters['BC']['northSide']['type']:
            defineSetOfVerticesByBoundingSphere(RVEpart,CornerBx,L+Lply,0.0,0.00001*Rf,'PLYINTERFACE-NE-CORNER',logfilepath,baselogindent + 4*logindent,True)
            defineSetOfVerticesByBoundingSphere(RVEpart,CornerAx,L+Lply,0.0,0.00001*Rf,'PLYINTERFACE-NW-CORNER',logfilepath,baselogindent + 4*logindent,True)
        else:
            defineSetOfVerticesByBoundingSphere(RVEpart,CornerBx,L,0.0,0.00001*Rf,'PLYINTERFACE-NE-CORNER',logfilepath,baselogindent + 4*logindent,True)
            defineSetOfVerticesByBoundingSphere(RVEpart,CornerAx,L,0.0,0.00001*Rf,'PLYINTERFACE-NW-CORNER',logfilepath,baselogindent + 4*logindent,True)
    if 'boundingPly' in parameters['BC']['rightSide']['type']:
        defineSetOfVerticesByBoundingSphere(RVEpart,L,L,0.0,0.00001*Rf,'RIGHTPLYINTERFACE-N-CORNER',logfilepath,baselogindent + 4*logindent,True)
    if 'boundingPly' in parameters['BC']['leftSide']['type']:
        defineSetOfVerticesByBoundingSphere(RVEpart,-L,L,0.0,0.00001*Rf,'LEFTPLYINTERFACE-N-CORNER',logfilepath,baselogindent + 4*logindent,True)

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    # sets of edges
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Sets of edges',True)

    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        alphaup = theta + deltatheta - deltapsi
        betaup = theta + deltatheta + deltapsi
        gammaup = theta + deltatheta + deltapsi + deltaphi
        alphalow = theta - deltatheta + deltapsi
        betalow = theta - deltatheta - deltapsi
        gammalow = theta - deltatheta - deltapsi + deltaphi
        setsOfEdgesData = [[0.99*Rf*np.cos(theta*np.pi/180),0.99*Rf*np.sin(theta*np.pi/180),0.0,1.01*Rf*np.cos(theta*np.pi/180),1.01*Rf*np.sin(theta*np.pi/180),0.0,'CRACK-CENTER'],   [0.99*Rf*np.cos((alphalow-0.5*deltapsi)*np.pi/180),0.99*Rf*np.sin((alphalow-0.5*deltapsi)*np.pi/180),0.0,1.01*Rf*np.cos((alphalow-0.5*deltapsi)*np.pi/180),1.01*Rf*np.sin((alphalow-0.5*deltapsi)*np.pi/180),0.0,'CRACK-LOWER'], [0.99*Rf*np.cos((alphaup+0.5*deltapsi)*np.pi/180),0.99*Rf*np.sin((alphaup+0.5*deltapsi)*np.pi/180),0.0,1.01*Rf*np.cos((alphaup+0.5*deltapsi)*np.pi/180),1.01*Rf*np.sin((alphaup+0.5*deltapsi)*np.pi/180),0.0,'CRACK-UPPER']]
        for setOfEdgesData in setsOfEdgesData:
            defineSetOfEdgesByClosestPoints(RVEpart,setOfEdgesData[0],setOfEdgesData[1],setOfEdgesData[2],setOfEdgesData[3],setOfEdgesData[4],setOfEdgesData[5],setOfEdgesData[-1],logfilepath,baselogindent + 4*logindent,True)
        RVEpart.SetByBoolean(name='CRACK', sets=[RVEpart.sets['CRACK-CENTER'],RVEpart.sets['CRACK-LOWER'],RVEpart.sets['CRACK-UPPER']])
    else:
        alpha = theta + deltatheta - deltapsi
        beta = theta + deltatheta + deltapsi
        gamma = theta + deltatheta + deltapsi + deltaphi
        setsOfEdgesData = [[0.99*Rf*np.cos(0.5*alpha*np.pi/180),0.99*Rf*np.sin(0.5*alpha*np.pi/180),0.0,1.01*Rf*np.cos(0.5*alpha*np.pi/180),1.01*Rf*np.sin(0.5*alpha*np.pi/180),0.0,'CRACK-LOWER'], [0.99*Rf*np.cos((alpha+0.5*deltapsi)*np.pi/180),0.99*Rf*np.sin((alpha+0.5*deltapsi)*np.pi/180),0.0,1.01*Rf*np.cos((alpha+0.5*deltapsi)*np.pi/180),1.01*Rf*np.sin((alpha+0.5*deltapsi)*np.pi/180),0.0,'CRACK-UPPER']]
        for setOfEdgesData in setsOfEdgesData:
            defineSetOfEdgesByClosestPoints(RVEpart,setOfEdgesData[0],setOfEdgesData[1],setOfEdgesData[2],setOfEdgesData[3],setOfEdgesData[4],setOfEdgesData[5],setOfEdgesData[-1],logfilepath,baselogindent + 4*logindent,True)
        RVEpart.SetByBoolean(name='CRACK', sets=[RVEpart.sets['CRACK-LOWER'],RVEpart.sets['CRACK-UPPER']])

    writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- CRACK',True)

    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        lowerSideSets = []
        setsOfEdgesData = [[0.001*Rf,-L+0.001,0.0,0.001*Rf,-L-0.001,0.0,'LOWERSIDE-CENTER']]
        if 'boundingPly' in parameters['BC']['rightSide']['type']:
            setsOfEdgesData.append([0.99*CornerBx,0.001,0.0,0.99*CornerBx,-0.001,0.0,'LOWERSIDE-RIGHT-HOMOGENIZED-PLY'])
        if 'boundingPly' in parameters['BC']['leftSide']['type']:
            setsOfEdgesData.append([0.99*CornerAx,0.001,0.0,0.99*CornerAx,-0.001,0.0,'LOWERSIDE-LEFT-HOMOGENIZED-PLY'])
        for setOfEdgesData in setsOfEdgesData:
            defineSetOfEdgesByClosestPoints(RVEpart,setOfEdgesData[0],setOfEdgesData[1],setOfEdgesData[2],setOfEdgesData[3],setOfEdgesData[4],setOfEdgesData[5],setOfEdgesData[-1],logfilepath,baselogindent + 4*logindent,True)
            lowerSideSets.append(RVEpart.sets[setOfEdgesData[-1]])
        RVEpart.SetByBoolean(name='LOWERSIDE', sets=lowerSideSets)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- LOWERSIDE',True)
    else:
        setsOfEdgesData = [[0.001*Rf,0.001,0.0,0.001*Rf,-0.001,0.0,'LOWERSIDE-CENTER'],
                           [0.65*Rf,0.001,0.0,0.65*Rf,-0.001,0.0,'LOWERSIDE-FIRSTRING-RIGHT'],
                           [0.99*L,0.001,0.0,0.99*L,-0.001,0.0,'LOWERSIDE-MATRIXBULK-RIGHT']]
        if 'half' in parameters['geometry']['fiber']['type']:
            setsOfEdgesData.append([-0.65*Rf,0.001,0.0,-0.65*Rf,-0.001,0.0,'LOWERSIDE-FIRSTRING-LEFT'])
            setsOfEdgesData.append([-0.99*L,0.001,0.0,-0.99*L,-0.001,0.0,'LOWERSIDE-MATRIXBULK-LEFT'])
        for setOfEdgesData in setsOfEdgesData:
            defineSetOfEdgesByClosestPoints(RVEpart,setOfEdgesData[0],setOfEdgesData[1],setOfEdgesData[2],setOfEdgesData[3],setOfEdgesData[4],setOfEdgesData[5],setOfEdgesData[-1],logfilepath,baselogindent + 4*logindent,True)
        if 'half' in parameters['geometry']['fiber']['type']:
            RVEpart.SetByBoolean(name='LOWERSIDE-FIRSTRING', sets=[RVEpart.sets['LOWERSIDE-FIRSTRING-RIGHT'],RVEpart.sets['LOWERSIDE-FIRSTRING-LEFT']])
        else:
            RVEpart.SetByBoolean(name='LOWERSIDE-FIRSTRING', sets=[RVEpart.sets['LOWERSIDE-FIRSTRING-RIGHT']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- LOWERSIDE-FIRSTRING',True)

        setsOfEdgesData = [[0.85*Rf,0.001,0.0,0.85*Rf,-0.001,0.0,'LOWERSIDE-SECONDRING-RIGHT']]
        if 'half' in parameters['geometry']['fiber']['type']:
            setsOfEdgesData.append([-0.85*Rf,0.001,0.0,-0.85*Rf,-0.001,0.0,'LOWERSIDE-SECONDRING-LEFT'])
        for setOfEdgesData in setsOfEdgesData:
            defineSetOfEdgesByClosestPoints(RVEpart,setOfEdgesData[0],setOfEdgesData[1],setOfEdgesData[2],setOfEdgesData[3],setOfEdgesData[4],setOfEdgesData[5],setOfEdgesData[-1],logfilepath,baselogindent + 4*logindent,True)
        if 'half' in parameters['geometry']['fiber']['type']:
            RVEpart.SetByBoolean(name='LOWERSIDE-SECONDRING', sets=[RVEpart.sets['LOWERSIDE-SECONDRING-RIGHT'],RVEpart.sets['LOWERSIDE-SECONDRING-LEFT']])
        else:
            RVEpart.SetByBoolean(name='LOWERSIDE-SECONDRING', sets=[RVEpart.sets['LOWERSIDE-SECONDRING-RIGHT']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- LOWERSIDE-SECONDRING',True)

        if L>2*Rf:
            R1 = (1+0.5*0.25)*Rf
            R2 = (1.25+0.5*0.25)*Rf
        else:
            R1 = Rf+0.5*0.25*(L-Rf)
            R2 = Rf+1.5*0.25*(L-Rf)

        setsOfEdgesData = [[R1,0.001,0.0,R1,-0.001,0.0,'LOWERSIDE-THIRDRING-RIGHT']]
        if 'half' in parameters['geometry']['fiber']['type']:
            setsOfEdgesData.append([-R1,0.001,0.0,-R1,-0.001,0.0,'LOWERSIDE-THIRDRING-LEFT'])
        for setOfEdgesData in setsOfEdgesData:
            defineSetOfEdgesByClosestPoints(RVEpart,setOfEdgesData[0],setOfEdgesData[1],setOfEdgesData[2],setOfEdgesData[3],setOfEdgesData[4],setOfEdgesData[5],setOfEdgesData[-1],logfilepath,baselogindent + 4*logindent,True)
        if 'half' in parameters['geometry']['fiber']['type']:
            RVEpart.SetByBoolean(name='LOWERSIDE-THIRDRING', sets=[RVEpart.sets['LOWERSIDE-THIRDRING-RIGHT'],RVEpart.sets['LOWERSIDE-THIRDRING-LEFT']])
        else:
            RVEpart.SetByBoolean(name='LOWERSIDE-THIRDRING', sets=[RVEpart.sets['LOWERSIDE-THIRDRING-RIGHT']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- LOWERSIDE-THIRDRING',True)

        setsOfEdgesData = [[R2,0.001,0.0,R2,-0.001,0.0,'LOWERSIDE-FOURTHRING-RIGHT']]
        if 'half' in parameters['geometry']['fiber']['type']:
            setsOfEdgesData.append([-R2,0.001,0.0,-R2,-0.001,0.0,'LOWERSIDE-FOURTHRING-LEFT'])
        for setOfEdgesData in setsOfEdgesData:
            defineSetOfEdgesByClosestPoints(RVEpart,setOfEdgesData[0],setOfEdgesData[1],setOfEdgesData[2],setOfEdgesData[3],setOfEdgesData[4],setOfEdgesData[5],setOfEdgesData[-1],logfilepath,baselogindent + 4*logindent,True)
        if 'half' in parameters['geometry']['fiber']['type']:
            RVEpart.SetByBoolean(name='LOWERSIDE-FOURTHRING', sets=[RVEpart.sets['LOWERSIDE-FOURTHRING-RIGHT'],RVEpart.sets['LOWERSIDE-FOURTHRING-LEFT']])
        else:
            RVEpart.SetByBoolean(name='LOWERSIDE-FOURTHRING', sets=[RVEpart.sets['LOWERSIDE-FOURTHRING-RIGHT']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- LOWERSIDE-FOURTHRING',True)

        lowerSideSets = [RVEpart.sets['LOWERSIDE-CENTER'],RVEpart.sets['LOWERSIDE-FIRSTRING'],RVEpart.sets['LOWERSIDE-SECONDRING'],RVEpart.sets['LOWERSIDE-THIRDRING'],RVEpart.sets['LOWERSIDE-FOURTHRING'],RVEpart.sets['LOWERSIDE-MATRIXBULK-RIGHT'],RVEpart.sets['LOWERSIDE-MATRIXBULK-LEFT']]
        setsOfEdgesData = []
        if 'boundingPly' in parameters['BC']['rightSide']['type']:
            setsOfEdgesData.append([0.99*CornerBx,0.001,0.0,0.99*CornerBx,-0.001,0.0,'LOWERSIDE-RIGHT-HOMOGENIZED-PLY'])
        if 'boundingPly' in parameters['BC']['leftSide']['type']:
            setsOfEdgesData.append([0.99*CornerAx,0.001,0.0,0.99*CornerAx,-0.001,0.0,'LOWERSIDE-LEFT-HOMOGENIZED-PLY'])
        if 'adjacentFibers' in parameters['BC']['rightSide']['type']:
            for nFiber in range(0,parameters['BC']['rightSide']['nFibers']):
                setsOfEdgesData.append([(nFiber+1)*2*L,0.001,0.0,(nFiber+1)*2*L,-0.001,0.0,'LOWERSIDE-RIGHT-FIBER'+str(nFiber+1)])
                setsOfEdgesData.append([(nFiber+1)*2*L+1.01*Rf,0.001,0.0,(nFiber+1)*2*L+1.01*Rf,-0.001,0.0,'LOWERSIDE-RIGHT-FIBER'+str(nFiber+1)+'-RIGHTMAT'])
        if 'adjacentFibers' in parameters['BC']['leftSide']['type']:
            for nFiber in range(0,parameters['BC']['leftSide']['nFibers']):
                setsOfEdgesData.append([-(nFiber+1)*2*L,0.001,0.0,-(nFiber+1)*2*L,-0.001,0.0,'LOWERSIDE-LEFT-FIBER'+str(nFiber+1)])
                setsOfEdgesData.append([-(nFiber+1)*2*L-1.01*Rf,0.001,0.0,-(nFiber+1)*2*L-1.01*Rf,-0.001,0.0,'LOWERSIDE-LEFT-FIBER'+str(nFiber+1)+'-LEFTMAT'])
        for setOfEdgesData in setsOfEdgesData:
            defineSetOfEdgesByClosestPoints(RVEpart,setOfEdgesData[0],setOfEdgesData[1],setOfEdgesData[2],setOfEdgesData[3],setOfEdgesData[4],setOfEdgesData[5],setOfEdgesData[-1],logfilepath,baselogindent + 4*logindent,True)
            lowerSideSets.append(RVEpart.sets[setOfEdgesData[-1]])
        RVEpart.SetByBoolean(name='LOWERSIDE', sets=lowerSideSets)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- LOWERSIDE',True)

    setsOfEdgesData = [[0.49*Rf*np.cos((theta+deltatheta)*np.pi/180),0.49*Rf*np.sin((theta+deltatheta)*np.pi/180),0.0,0.51*Rf*np.cos((theta+deltatheta)*np.pi/180),0.51*Rf*np.sin((theta+deltatheta)*np.pi/180),0.0,'FIRSTCIRCLE']]
    if L>2*Rf:
        setsOfEdgesData.append([1.49*Rf*np.cos((theta+deltatheta)*np.pi/180),1.49*Rf*np.sin((theta+deltatheta)*np.pi/180),0.0,1.51*Rf*np.cos((theta+deltatheta)*np.pi/180),1.51*Rf*np.sin((theta+deltatheta)*np.pi/180),0.0,'FIFTHCIRCLE'])
    else:
        setsOfEdgesData.append([(Rf+0.49*(L-Rf))*np.cos((theta+deltatheta)*np.pi/180),(Rf+0.49*(L-Rf))*np.sin((theta+deltatheta)*np.pi/180),0.0,(Rf+0.51*(L-Rf))*np.cos((theta+deltatheta)*np.pi/180),(Rf+0.51*(L-Rf))*np.sin((theta+deltatheta)*np.pi/180),0.0,'FIFTHCIRCLE'])
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        ctNames = ['CTUP','CTLOW']
        circleNames = ['SECOND','THIRD','FOURTH']
        alphas = [theta + deltatheta - deltapsi,theta - deltatheta + deltapsi]
        ctAngles = [theta + deltatheta,theta - deltatheta]
        betas = [theta + deltatheta + deltapsi,theta - deltatheta - deltapsi]
        gammas = [theta + deltatheta + deltapsi + deltaphi,theta - deltatheta - deltapsi - deltaphi]
        incs = [1.0,-1.0]
        if L>2*Rf:
            R4 = 1.25*Rf
        else:
            R4 = Rf+0.25*(L-Rf)
        radiuses = [0.75*Rf,Rf,R4]
        for rIndex,rValue in enumerate(radiuses):
            for aIndex,aValue in enumerate(alphas):
                setsOfEdgesData.append([0.99*rValue*np.cos((alphas[aIndex]+incs[aIndex])*np.pi/180),0.99*rValue*np.sin((alphas[aIndex]+incs[aIndex])*np.pi/180),0.0,1.01*rValue*np.cos((alphas[aIndex]+incs[aIndex])*np.pi/180),1.01*rValue*np.sin((alphas[aIndex]+incs[aIndex])*np.pi/180),0.0,circleNames[rIndex]+'CIRCLE-UPPERCRACK-'+ctNames[aIndex]])
                setsOfEdgesData.append([0.99*rValue*np.cos((ctAngles[aIndex]+incs[aIndex])*np.pi/180),0.99*rValue*np.sin((ctAngles[aIndex]+incs[aIndex])*np.pi/180),0.0,1.01*rValue*np.cos((ctAngles[aIndex]+incs[aIndex])*np.pi/180),1.01*rValue*np.sin((ctAngles[aIndex]+incs[aIndex])*np.pi/180),0.0,circleNames[rIndex]+'CIRCLE-FIRSTBOUNDED-'+ctNames[aIndex]])
                setsOfEdgesData.append([0.99*rValue*np.cos((betas[aIndex]+incs[aIndex])*np.pi/180),0.99*rValue*np.sin((betas[aIndex]+incs[aIndex])*np.pi/180),0.0,1.01*rValue*np.cos((betas[aIndex]+incs[aIndex])*np.pi/180),1.01*rValue*np.sin((betas[aIndex]+incs[aIndex])*np.pi/180),0.0,circleNames[rIndex]+'CIRCLE-SECONDBOUNDED-'+ctNames[aIndex]])
            setsOfEdgesData.append([0.99*rValue*np.cos(theta*np.pi/180),0.99*rValue*np.sin(theta*np.pi/180),0.0,1.01*rValue*np.cos(theta*np.pi/180),1.01*rValue*np.sin(theta*np.pi/180),0.0,circleNames[rIndex]+'CIRCLE-CENTERCRACK'])
            setsOfEdgesData.append([0.99*rValue*np.cos(1.025*gammas[0]*np.pi/180),0.99*rValue*np.sin(1.025*gammas[0]*np.pi/180),0.0,1.01*rValue*np.cos(1.025*gammas[0]*np.pi/180),1.01*rValue*np.sin(1.025*gammas[0]*np.pi/180),0.0,circleNames[rIndex]+'CIRCLE-RESTBOUNDED'])
        for aIndex,aValue in enumerate(alphas):
            setsOfEdgesData.append([0.85*Rf*np.cos(0.99*alphas[aIndex]*np.pi/180),0.85*Rf*np.sin(0.99*alphas[aIndex]*np.pi/180),0.0,0.85*Rf*np.cos(1.01*alphas[aIndex]*np.pi/180),0.85*Rf*np.sin(1.01*alphas[aIndex]*np.pi/180),0.0,'TRANSVERSALCUT-FIRSTFIBER-'+ctNames[aIndex]])
            setsOfEdgesData.append([1.05*Rf*np.cos(0.99*alphas[aIndex]*np.pi/180),1.05*Rf*np.sin(0.99*alphas[aIndex]*np.pi/180),0.0,1.05*Rf*np.cos(1.01*alphas[aIndex]*np.pi/180),1.05*Rf*np.sin(1.01*alphas[aIndex]*np.pi/180),0.0,'TRANSVERSALCUT-FIRSTMATRIX-'+ctNames[aIndex]])
            setsOfEdgesData.append([0.85*Rf*np.cos(0.99*ctAngles[aIndex]*np.pi/180),0.85*Rf*np.sin(0.99*ctAngles[aIndex]*np.pi/180),0.0,0.85*Rf*np.cos(1.01*ctAngles[aIndex]*np.pi/180),0.85*Rf*np.sin(1.01*ctAngles[aIndex]*np.pi/180),0.0,'TRANSVERSALCUT-SECONDFIBER-'+ctNames[aIndex]])
            setsOfEdgesData.append([1.05*Rf*np.cos(0.99*ctAngles[aIndex]*np.pi/180),1.05*Rf*np.sin(0.99*ctAngles[aIndex]*np.pi/180),0.0,1.05*Rf*np.cos(1.01*ctAngles[aIndex]*np.pi/180),1.05*Rf*np.sin(1.01*ctAngles[aIndex]*np.pi/180),0.0,'TRANSVERSALCUT-SECONDMATRIX-'+ctNames[aIndex]])
            setsOfEdgesData.append([0.85*Rf*np.cos(0.99*betas[aIndex]*np.pi/180),0.85*Rf*np.sin(0.99*betas[aIndex]*np.pi/180),0.0,0.85*Rf*np.cos(1.01*betas[aIndex]*np.pi/180),0.85*Rf*np.sin(1.01*betas[aIndex]*np.pi/180),0.0,'TRANSVERSALCUT-THIRDFIBER-'+ctNames[aIndex]])
            setsOfEdgesData.append([1.05*Rf*np.cos(0.99*betas[aIndex]*np.pi/180),1.05*Rf*np.sin(0.99*betas[aIndex]*np.pi/180),0.0,1.05*Rf*np.cos(1.01*betas[aIndex]*np.pi/180),1.05*Rf*np.sin(1.01*betas[aIndex]*np.pi/180),0.0,'TRANSVERSALCUT-THIRDMATRIX-'+ctNames[aIndex]])
            setsOfEdgesData.append([0.85*Rf*np.cos(0.99*gammas[aIndex]*np.pi/180),0.85*Rf*np.sin(0.99*gammas[aIndex]*np.pi/180),0.0,0.85*Rf*np.cos(1.01*gammas[aIndex]*np.pi/180),0.85*Rf*np.sin(1.01*gammas[aIndex]*np.pi/180),0.0,'TRANSVERSALCUT-FOURTHFIBER-'+ctNames[aIndex]])
            setsOfEdgesData.append([1.05*Rf*np.cos(0.99*gammas[aIndex]*np.pi/180),1.05*Rf*np.sin(0.99*gammas[aIndex]*np.pi/180),0.0,1.05*Rf*np.cos(1.01*gammas[aIndex]*np.pi/180),1.05*Rf*np.sin(1.01*gammas[aIndex]*np.pi/180),0.0,'TRANSVERSALCUT-FOURTHMATRIX-'+ctNames[aIndex]])
    else:
        alpha = theta + deltatheta - deltapsi
        beta = theta + deltatheta + deltapsi
        gamma = theta + deltatheta + deltapsi + deltaphi
        setsOfEdgesData.append([0.74*Rf*np.cos(0.5*alpha*np.pi/180),0.74*Rf*np.sin(0.5*alpha*np.pi/180),0.0,0.76*Rf*np.cos(0.5*alpha*np.pi/180),0.76*Rf*np.sin(0.5*alpha*np.pi/180),0.0,'SECONDCIRCLE-LOWERCRACK'])
        setsOfEdgesData.append([0.74*Rf*np.cos((alpha+0.5*deltapsi)*np.pi/180),0.74*Rf*np.sin((alpha+0.5*deltapsi)*np.pi/180),0.0,0.76*Rf*np.cos((alpha+0.5*deltapsi)*np.pi/180),0.76*Rf*np.sin((alpha+0.5*deltapsi)*np.pi/180),0.0,'SECONDCIRCLE-UPPERCRACK'])
        setsOfEdgesData.append([0.74*Rf*np.cos((theta+deltatheta+0.5*deltapsi)*np.pi/180),0.74*Rf*np.sin((theta+deltatheta+0.5*deltapsi)*np.pi/180),0.0,0.76*Rf*np.cos((theta+deltatheta+0.5*deltapsi)*np.pi/180),0.76*Rf*np.sin((theta+deltatheta+0.5*deltapsi)*np.pi/180),0.0,'SECONDCIRCLE-FIRSTBOUNDED'])
        setsOfEdgesData.append([0.74*Rf*np.cos((beta+0.5*deltaphi)*np.pi/180),0.74*Rf*np.sin((beta+0.5*deltaphi)*np.pi/180),0.0,0.76*Rf*np.cos((beta+0.5*deltaphi)*np.pi/180),0.76*Rf*np.sin((beta+0.5*deltaphi)*np.pi/180),0.0,'SECONDCIRCLE-SECONDBOUNDED'])
        setsOfEdgesData.append([0.74*Rf*np.cos(1.025*gamma*np.pi/180),0.74*Rf*np.sin(1.025*gamma*np.pi/180),0.0,0.76*Rf*np.cos(1.025*gamma*np.pi/180),0.76*Rf*np.sin(1.025*gamma*np.pi/180),0.0,'SECONDCIRCLE-RESTBOUNDED'])
        setsOfEdgesData.append([0.99*Rf*np.cos(0.5*alpha*np.pi/180),0.99*Rf*np.sin(0.5*alpha*np.pi/180),0.0,1.01*Rf*np.cos(0.5*alpha*np.pi/180),1.01*Rf*np.sin(0.5*alpha*np.pi/180),0.0,'THIRDCIRCLE-LOWERCRACK'])
        setsOfEdgesData.append([0.99*Rf*np.cos((alpha+0.5*deltapsi)*np.pi/180),0.99*Rf*np.sin((alpha+0.5*deltapsi)*np.pi/180),0.0,1.01*Rf*np.cos((alpha+0.5*deltapsi)*np.pi/180),1.01*Rf*np.sin((alpha+0.5*deltapsi)*np.pi/180),0.0,'THIRDCIRCLE-UPPERCRACK'])
        setsOfEdgesData.append([0.99*Rf*np.cos((theta+deltatheta+0.5*deltapsi)*np.pi/180),0.99*Rf*np.sin((theta+deltatheta+0.5*deltapsi)*np.pi/180),0.0,1.01*Rf*np.cos((theta+deltatheta+0.5*deltapsi)*np.pi/180),1.01*Rf*np.sin((theta+deltatheta+0.5*deltapsi)*np.pi/180),0.0,'THIRDCIRCLE-FIRSTBOUNDED'])
        setsOfEdgesData.append([0.99*Rf*np.cos((beta+0.5*deltaphi)*np.pi/180),0.99*Rf*np.sin((beta+0.5*deltaphi)*np.pi/180),0.0,1.01*Rf*np.cos((beta+0.5*deltaphi)*np.pi/180),1.01*Rf*np.sin((beta+0.5*deltaphi)*np.pi/180),0.0,'THIRDCIRCLE-SECONDBOUNDED'])
        setsOfEdgesData.append([0.99*Rf*np.cos((gamma+0.5*(180.0-gamma))*np.pi/180),0.99*Rf*np.sin((gamma+0.5*(180.0-gamma))*np.pi/180),0.0,1.01*Rf*np.cos((gamma+0.5*(180.0-gamma))*np.pi/180),1.01*Rf*np.sin((gamma+0.5*(180.0-gamma))*np.pi/180),0.0,'THIRDCIRCLE-RESTBOUNDED'])
        if L>2*Rf:
            R4 = 1.25*Rf
        else:
            R4 = Rf+0.25*(L-Rf)
        setsOfEdgesData.append([0.99*R4*np.cos(0.5*alpha*np.pi/180),0.99*R4*np.sin(0.5*alpha*np.pi/180),0.0,1.01*R4*np.cos(0.5*alpha*np.pi/180),1.01*R4*np.sin(0.5*alpha*np.pi/180),0.0,'FOURTHCIRCLE-LOWERCRACK'])
        setsOfEdgesData.append([0.99*R4*np.cos((alpha+0.5*deltapsi)*np.pi/180),0.99*R4*np.sin((alpha+0.5*deltapsi)*np.pi/180),0.0,1.01*R4*np.cos((alpha+0.5*deltapsi)*np.pi/180),1.01*R4*np.sin((alpha+0.5*deltapsi)*np.pi/180),0.0,'FOURTHCIRCLE-UPPERCRACK'])
        setsOfEdgesData.append([0.99*R4*np.cos((theta+deltatheta+0.5*deltapsi)*np.pi/180),0.99*R4*np.sin((theta+deltatheta+0.5*deltapsi)*np.pi/180),0.0,1.01*R4*np.cos((theta+deltatheta+0.5*deltapsi)*np.pi/180),1.01*R4*np.sin((theta+deltatheta+0.5*deltapsi)*np.pi/180),0.0,'FOURTHCIRCLE-FIRSTBOUNDED'])
        setsOfEdgesData.append([0.99*R4*np.cos((beta+0.5*deltaphi)*np.pi/180),0.99*R4*np.sin((beta+0.5*deltaphi)*np.pi/180),0.0,1.01*R4*np.cos((beta+0.5*deltaphi)*np.pi/180),1.01*R4*np.sin((beta+0.5*deltaphi)*np.pi/180),0.0,'FOURTHCIRCLE-SECONDBOUNDED'])
        setsOfEdgesData.append([0.99*R4*np.cos((gamma+0.5*(180.0-gamma))*np.pi/180),0.99*R4*np.sin((gamma+0.5*(180.0-gamma))*np.pi/180),0.0,1.01*R4*np.cos((gamma+0.5*(180.0-gamma))*np.pi/180),1.01*R4*np.sin((gamma+0.5*(180.0-gamma))*np.pi/180),0.0,'FOURTHCIRCLE-RESTBOUNDED'])
        setsOfEdgesData.append([0.85*Rf*np.cos(0.99*alpha*np.pi/180),0.85*Rf*np.sin(0.99*alpha*np.pi/180),0.0,0.85*Rf*np.cos(1.01*alpha*np.pi/180),0.85*Rf*np.sin(1.01*alpha*np.pi/180),0.0,'TRANSVERSALCUT-FIRSTFIBER'])
        setsOfEdgesData.append([1.05*Rf*np.cos(0.99*alpha*np.pi/180),1.05*Rf*np.sin(0.99*alpha*np.pi/180),0.0,1.05*Rf*np.cos(1.01*alpha*np.pi/180),1.05*Rf*np.sin(1.01*alpha*np.pi/180),0.0,'TRANSVERSALCUT-FIRSTMATRIX'])
        setsOfEdgesData.append([0.85*Rf*np.cos(0.99*(theta+deltatheta)*np.pi/180),0.85*Rf*np.sin(0.99*(theta+deltatheta)*np.pi/180),0.0,0.85*Rf*np.cos(1.01*(theta+deltatheta)*np.pi/180),0.85*Rf*np.sin(1.01*(theta+deltatheta)*np.pi/180),0.0,'TRANSVERSALCUT-SECONDFIBER'])
        setsOfEdgesData.append([1.05*Rf*np.cos(0.99*(theta+deltatheta)*np.pi/180),1.05*Rf*np.sin(0.99*(theta+deltatheta)*np.pi/180),0.0,1.05*Rf*np.cos(1.01*(theta+deltatheta)*np.pi/180),1.05*Rf*np.sin(1.01*(theta+deltatheta)*np.pi/180),0.0,'TRANSVERSALCUT-SECONDMATRIX'])
        setsOfEdgesData.append([0.85*Rf*np.cos(0.99*beta*np.pi/180),0.85*Rf*np.sin(0.99*beta*np.pi/180),0.0,0.85*Rf*np.cos(1.01*beta*np.pi/180),0.85*Rf*np.sin(1.01*beta*np.pi/180),0.0,'TRANSVERSALCUT-THIRDFIBER'])
        setsOfEdgesData.append([1.05*Rf*np.cos(0.99*beta*np.pi/180),1.05*Rf*np.sin(0.99*beta*np.pi/180),0.0,1.05*Rf*np.cos(1.01*beta*np.pi/180),1.05*Rf*np.sin(1.01*beta*np.pi/180),0.0,'TRANSVERSALCUT-THIRDMATRIX'])
        setsOfEdgesData.append([0.85*Rf*np.cos(0.99*gamma*np.pi/180),0.85*Rf*np.sin(0.99*gamma*np.pi/180),0.0,0.85*Rf*np.cos(1.01*gamma*np.pi/180),0.85*Rf*np.sin(1.01*gamma*np.pi/180),0.0,'TRANSVERSALCUT-FOURTHFIBER'])
        setsOfEdgesData.append([1.05*Rf*np.cos(0.99*gamma*np.pi/180),1.05*Rf*np.sin(0.99*gamma*np.pi/180),0.0,1.05*Rf*np.cos(1.01*gamma*np.pi/180),1.05*Rf*np.sin(1.01*gamma*np.pi/180),0.0,'TRANSVERSALCUT-FOURTHMATRIX'])

    for setOfEdgesData in setsOfEdgesData:
        defineSetOfEdgesByClosestPoints(RVEpart,setOfEdgesData[0],setOfEdgesData[1],setOfEdgesData[2],setOfEdgesData[3],setOfEdgesData[4],setOfEdgesData[5],setOfEdgesData[-1],logfilepath,baselogindent + 4*logindent,True)
    setsOfEdgesData = []

    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        RVEpart.SetByBoolean(name='SECONDCIRCLE', sets=[RVEpart.sets['SECONDCIRCLE-CENTERCRACK'],RVEpart.sets['SECONDCIRCLE-UPPERCRACK-CTUP'],RVEpart.sets['SECONDCIRCLE-FIRSTBOUNDED-CTUP'],RVEpart.sets['SECONDCIRCLE-SECONDBOUNDED-CTUP'],RVEpart.sets['SECONDCIRCLE-UPPERCRACK-CTLOW'],RVEpart.sets['SECONDCIRCLE-FIRSTBOUNDED-CTLOW'],RVEpart.sets['SECONDCIRCLE-SECONDBOUNDED-CTLOW'],RVEpart.sets['SECONDCIRCLE-RESTBOUNDED']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- SECONDCIRCLE',True)
        RVEpart.SetByBoolean(name='THIRDCIRCLE', sets=[RVEpart.sets['THIRDCIRCLE-CENTERCRACK'],RVEpart.sets['THIRDCIRCLE-UPPERCRACK-CTUP'],RVEpart.sets['THIRDCIRCLE-FIRSTBOUNDED-CTUP'],RVEpart.sets['THIRDCIRCLE-SECONDBOUNDED-CTUP'],RVEpart.sets['THIRDCIRCLE-UPPERCRACK-CTLOW'],RVEpart.sets['THIRDCIRCLE-FIRSTBOUNDED-CTLOW'],RVEpart.sets['THIRDCIRCLE-SECONDBOUNDED-CTLOW'],RVEpart.sets['THIRDCIRCLE-RESTBOUNDED']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- THIRDCIRCLE',True)
        RVEpart.SetByBoolean(name='FOURTHCIRCLE', sets=[RVEpart.sets['FOURTHCIRCLE-CENTERCRACK'],RVEpart.sets['FOURTHCIRCLE-UPPERCRACK-CTUP'],RVEpart.sets['FOURTHCIRCLE-FIRSTBOUNDED-CTUP'],RVEpart.sets['FOURTHCIRCLE-SECONDBOUNDED-CTUP'],RVEpart.sets['FOURTHCIRCLE-UPPERCRACK-CTLOW'],RVEpart.sets['FOURTHCIRCLE-FIRSTBOUNDED-CTLOW'],RVEpart.sets['FOURTHCIRCLE-SECONDBOUNDED-CTLOW'],RVEpart.sets['FOURTHCIRCLE-RESTBOUNDED']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- FOURTHCIRCLE',True)
    else:
        RVEpart.SetByBoolean(name='SECONDCIRCLE', sets=[RVEpart.sets['SECONDCIRCLE-LOWERCRACK'],RVEpart.sets['SECONDCIRCLE-UPPERCRACK'],RVEpart.sets['SECONDCIRCLE-FIRSTBOUNDED'],RVEpart.sets['SECONDCIRCLE-SECONDBOUNDED'],RVEpart.sets['SECONDCIRCLE-RESTBOUNDED']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- SECONDCIRCLE',True)
        RVEpart.SetByBoolean(name='THIRDCIRCLE', sets=[RVEpart.sets['THIRDCIRCLE-LOWERCRACK'],RVEpart.sets['THIRDCIRCLE-UPPERCRACK'],RVEpart.sets['THIRDCIRCLE-FIRSTBOUNDED'],RVEpart.sets['THIRDCIRCLE-SECONDBOUNDED'],RVEpart.sets['THIRDCIRCLE-RESTBOUNDED']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- THIRDCIRCLE',True)
        RVEpart.SetByBoolean(name='FOURTHCIRCLE', sets=[RVEpart.sets['FOURTHCIRCLE-LOWERCRACK'],RVEpart.sets['FOURTHCIRCLE-UPPERCRACK'],RVEpart.sets['FOURTHCIRCLE-FIRSTBOUNDED'],RVEpart.sets['FOURTHCIRCLE-SECONDBOUNDED'],RVEpart.sets['FOURTHCIRCLE-RESTBOUNDED']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- FOURTHCIRCLE',True)

    if ('boundingPly' in parameters['BC']['rightSide']['type'] or 'boundingPly' in parameters['BC']['leftSide']['type']) and not 'boundingPly' in parameters['BC']['northSide']['type']:
        setsOfEdgesData.append([0.0,0.99999*CornerBy,0.0,0.0,1.00001*CornerBy,0.0,'CENTER-RUC-UPPERSIDE'])
        if 'boundingPly' in parameters['BC']['rightSide']['type']:
            setsOfEdgesData.append([0.99999*CornerBx,0.99999*CornerBy,0.0,0.99999*CornerBx,1.00001*CornerBy,0.0,'RIGHT-HOMOPLY-UPPERSIDE'])
        if 'boundingPly' in parameters['BC']['leftSide']['type']:
            setsOfEdgesData.append([0.99999*CornerAx,0.99999*CornerBy,0.0,0.99999*CornerAx,1.00001*CornerBy,0.0,'LEFT-HOMOPLY-UPPERSIDE'])
    else:
        setsOfEdgesData.append([0.0,0.99999*CornerBy,0.0,0.0,1.00001*CornerBy,0.0,'UPPERSIDE'])
    if 'boundingPly' in parameters['BC']['northSide']['type']:
        if 'adjacentFibers' in parameters['BC']['northSide']['type']:
            setsOfEdgesData.append([0.001,0.99999*(L+Lply),0.0,0.001,1.00001*(L+Lply),0.0,'PLYINTERFACE'])
            setsOfEdgesData.append([0.99999*CornerBx,0.5*L,0.0,1.00001*CornerBx,0.5*L,0.0,'LOWER-RIGHTSIDE'])
            setsOfEdgesData.append([0.99999*CornerAx,0.5*L,0.0,1.00001*CornerAx,0.5*L,0.0,'LOWER-LEFTSIDE'])
            setsOfEdgesData.append([0.99999*CornerBx,(L+Lply)+0.5*Ludply,0.0,1.00001*CornerBx,(L+Lply)+0.5*Ludply,0.0,'UPPER-RIGHTSIDE'])
            setsOfEdgesData.append([0.99999*CornerAx,(L+Lply)+0.5*Ludply,0.0,1.00001*CornerAx,(L+Lply)+0.5*Ludply,0.0,'UPPER-LEFTSIDE'])
        else:
            setsOfEdgesData.append([0.001,0.99999*L,0.0,0.001,1.00001*L,0.0,'PLYINTERFACE'])
            setsOfEdgesData.append([0.99999*CornerBx,0.5*L,0.0,1.00001*CornerBx,0.5*L,0.0,'LOWER-RIGHTSIDE'])
            setsOfEdgesData.append([0.99999*CornerAx,0.5*L,0.0,1.00001*CornerAx,0.5*L,0.0,'LOWER-LEFTSIDE'])
            setsOfEdgesData.append([0.99999*CornerBx,L+0.5*Lply,0.0,1.00001*CornerBx,L+0.5*Lply,0.0,'UPPER-RIGHTSIDE'])
            setsOfEdgesData.append([0.99999*CornerAx,L+0.5*Lply,0.0,1.00001*CornerAx,L+0.5*Lply,0.0,'UPPER-LEFTSIDE'])
    else:
        setsOfEdgesData.append([0.99999*CornerBx,0.5*L,0.0,1.00001*CornerBx,0.5*L,0.0,'RIGHTSIDE'])
        setsOfEdgesData.append([0.99999*CornerAx,0.5*L,0.0,1.00001*CornerAx,0.5*L,0.0,'LEFTSIDE'])
    if 'adjacentFibers' in parameters['BC']['northSide']['type']:
        for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
            setsOfEdgesData.append([0.99*Rf,(nFiber+1)*2*L,0.0,1.01*Rf,(nFiber+1)*2*L,0.0,'INTERFACE-UPPER-FIBER-C'+str(nFiber+1)])
        if 'adjacentFibers' in parameters['BC']['rightSide']['type']:
            for mFiber in range(0,parameters['BC']['rightSide']['nFibers']):
                for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
                    setsOfEdgesData.append([(mFiber+1)*2*L+0.99*Rf,(nFiber+1)*2*L,0.0,(mFiber+1)*2*L+1.01*Rf,(nFiber+1)*2*L,0.0,'INTERFACE-UPPER-FIBER-R'+str(int(nFiber+1+mFiber*parameters['BC']['northSide']['nFibers']))])
        if 'adjacentFibers' in parameters['BC']['leftSide']['type']:
            Nfibers = parameters['BC']['northSide']['nFibers']
            for mFiber in range(0,parameters['BC']['leftSide']['nFibers']):
                for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
                    setsOfEdgesData.append([-(mFiber+1)*2*L+0.99*Rf,(nFiber+1)*2*L,0.0,-(mFiber+1)*2*L+1.01*Rf,(nFiber+1)*2*L,0.0,'INTERFACE-UPPER-FIBER-L'+str(int(nFiber+1+mFiber*parameters['BC']['northSide']['nFibers']))])

    for setOfEdgesData in setsOfEdgesData:
        defineSetOfEdgesByClosestPoints(RVEpart,setOfEdgesData[0],setOfEdgesData[1],setOfEdgesData[2],setOfEdgesData[3],setOfEdgesData[4],setOfEdgesData[5],setOfEdgesData[-1],logfilepath,baselogindent + 4*logindent,True)
    setsOfEdgesData = []

    if ('boundingPly' in parameters['BC']['rightSide']['type'] or 'boundingPly' in parameters['BC']['leftSide']['type']) and not 'boundingPly' in parameters['BC']['northSide']['type']:
        if 'boundingPly' in parameters['BC']['rightSide']['type'] and 'boundingPly' in parameters['BC']['leftSide']:
            RVEpart.SetByBoolean(name='UPPERSIDE', sets=[RVEpart.sets['CENTER-RUC-UPPERSIDE'],RVEpart.sets['RIGHT-HOMOPLY-UPPERSIDE'],RVEpart.sets['LEFT-HOMOPLY-UPPERSIDE']])
        elif 'boundingPly' in parameters['BC']['rightSide']['type']:
            RVEpart.SetByBoolean(name='UPPERSIDE', sets=[RVEpart.sets['CENTER-RUC-UPPERSIDE'],RVEpart.sets['RIGHT-HOMOPLY-UPPERSIDE']])
        elif 'boundingPly' in parameters['BC']['leftSide']['type']:
            RVEpart.SetByBoolean(name='UPPERSIDE', sets=[RVEpart.sets['CENTER-RUC-UPPERSIDE'],RVEpart.sets['LEFT-HOMOPLY-UPPERSIDE']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- UPPERSIDE',True)

    if 'boundingPly' in parameters['BC']['northSide']['type']:
        RVEpart.SetByBoolean(name='RIGHTSIDE', sets=[RVEpart.sets['LOWER-RIGHTSIDE'],RVEpart.sets['UPPER-RIGHTSIDE']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- RIGHTSIDE',True)
        RVEpart.SetByBoolean(name='LEFTSIDE', sets=[RVEpart.sets['LOWER-LEFTSIDE'],RVEpart.sets['UPPER-LEFTSIDE']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- LEFTSIDE',True)

    # sets of faces
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Sets of faces',True)

    setsOfFacesData = [[0.01*Rf, 0.25*Rf, 0,'FIBER-CENTER'],
                       [0.0, 0.65*Rf, 0,'FIBER-INTERMEDIATEANNULUS']]
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        setsOfFacesData.append([0.85*Rf*np.cos(theta*np.pi/180), 0.85*Rf*np.sin(theta*np.pi/180), 0,'FIBER-EXTANNULUS-CENTERCRACK'])
        setsOfFacesData.append([0.85*Rf*np.cos((theta+deltatheta-0.5*deltapsi)*np.pi/180), 0.85*Rf*np.sin((theta+deltatheta-0.5*deltapsi)*np.pi/180), 0,'FIBER-EXTANNULUS-UPPERCRACK-CTUP'])
        setsOfFacesData.append([0.85*Rf*np.cos((theta+deltatheta+0.5*deltapsi)*np.pi/180), 0.85*Rf*np.sin((theta+deltatheta+0.5*deltapsi)*np.pi/180), 0,'FIBER-EXTANNULUS-FIRSTBOUNDED-CTUP'])
        setsOfFacesData.append([0.85*Rf*np.cos((theta+deltatheta+deltapsi+0.5*deltaphi)*np.pi/180), 0.85*Rf*np.sin((theta+deltatheta+deltapsi+0.5*deltaphi)*np.pi/180), 0,'FIBER-EXTANNULUS-SECONDBOUNDED-CTUP'])
        setsOfFacesData.append([0.85*Rf*np.cos((theta-deltatheta+0.5*deltapsi)*np.pi/180), 0.85*Rf*np.sin((theta-deltatheta+0.5*deltapsi)*np.pi/180), 0,'FIBER-EXTANNULUS-UPPERCRACK-CTLOW'])
        setsOfFacesData.append([0.85*Rf*np.cos((theta-deltatheta-0.5*deltapsi)*np.pi/180), 0.85*Rf*np.sin((theta-deltatheta-0.5*deltapsi)*np.pi/180), 0,'FIBER-EXTANNULUS-FIRSTBOUNDED-CTLOW'])
        setsOfFacesData.append([0.85*Rf*np.cos((theta-deltatheta-deltapsi-0.5*deltaphi)*np.pi/180), 0.85*Rf*np.sin((theta-deltatheta-deltapsi-0.5*deltaphi)*np.pi/180), 0,'FIBER-EXTANNULUS-SECONDBOUNDED-CTLOW'])
        setsOfFacesData.append([0.85*Rf*np.cos((theta+deltatheta+deltapsi+deltaphi+1.0)*np.pi/180), 0.85*Rf*np.sin((theta+deltatheta+deltapsi+deltaphi+1.0)*np.pi/180), 0,'FIBER-EXTANNULUS-RESTBOUNDED'])
    else:
        alpha = theta + deltatheta - deltapsi
        beta = theta + deltatheta + deltapsi
        gamma = theta + deltatheta + deltapsi + deltaphi
        setsOfFacesData.append([0.85*Rf*np.cos(0.5*alpha*np.pi/180), 0.85*Rf*np.sin(0.5*alpha*np.pi/180), 0,'FIBER-EXTANNULUS-LOWERCRACK'])
        setsOfFacesData.append([0.85*Rf*np.cos((alpha+0.5*deltapsi)*np.pi/180), 0.85*Rf*np.sin((alpha+0.5*deltapsi)*np.pi/180), 0,'FIBER-EXTANNULUS-UPPERCRACK'])
        setsOfFacesData.append([0.85*Rf*np.cos((theta+deltatheta+0.5*deltapsi)*np.pi/180), 0.85*Rf*np.sin((theta+deltatheta+0.5*deltapsi)*np.pi/180), 0,'FIBER-EXTANNULUS-FIRSTBOUNDED'])
        setsOfFacesData.append([0.85*Rf*np.cos((beta+0.5*deltaphi)*np.pi/180), 0.85*Rf*np.sin((beta+0.5*deltaphi)*np.pi/180), 0,'FIBER-EXTANNULUS-SECONDBOUNDED'])
        setsOfFacesData.append([0.85*Rf*np.cos((gamma+0.5*(180-gamma))*np.pi/180), 0.85*Rf*np.sin((gamma+0.5*(180-gamma))*np.pi/180), 0,'FIBER-EXTANNULUS-RESTBOUNDED'])
    for setOfFacesData in setsOfFacesData:
        defineSetOfFacesByFindAt(RVEpart,setOfFacesData[0],setOfFacesData[1],setOfFacesData[2],setOfFacesData[-1],logfilepath,baselogindent + 4*logindent,True)

    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        RVEpart.SetByBoolean(name='FIBER-EXTANNULUS', sets=[RVEpart.sets['FIBER-EXTANNULUS-CENTERCRACK'],RVEpart.sets['FIBER-EXTANNULUS-UPPERCRACK-CTUP'],RVEpart.sets['FIBER-EXTANNULUS-FIRSTBOUNDED-CTUP'],RVEpart.sets['FIBER-EXTANNULUS-SECONDBOUNDED-CTUP'],RVEpart.sets['FIBER-EXTANNULUS-UPPERCRACK-CTLOW'],RVEpart.sets['FIBER-EXTANNULUS-FIRSTBOUNDED-CTLOW'],RVEpart.sets['FIBER-EXTANNULUS-SECONDBOUNDED-CTLOW'],RVEpart.sets['FIBER-EXTANNULUS-RESTBOUNDED']])
    else:
        RVEpart.SetByBoolean(name='FIBER-EXTANNULUS', sets=[RVEpart.sets['FIBER-EXTANNULUS-LOWERCRACK'],RVEpart.sets['FIBER-EXTANNULUS-UPPERCRACK'],RVEpart.sets['FIBER-EXTANNULUS-FIRSTBOUNDED'],RVEpart.sets['FIBER-EXTANNULUS-SECONDBOUNDED'],RVEpart.sets['FIBER-EXTANNULUS-RESTBOUNDED']])
    writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- FIBER-EXTANNULUS',True)
    RVEpart.SetByBoolean(name='FIBER', sets=[RVEpart.sets['FIBER-CENTER'],RVEpart.sets['FIBER-INTERMEDIATEANNULUS'],RVEpart.sets['FIBER-EXTANNULUS']])
    writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- FIBER',True)

    if L>2*Rf:
        R1 = (1+0.5*0.25)*Rf
        R2 = (1.25+0.5*0.25)*Rf
    else:
        R1 = Rf+0.5*0.25*(L-Rf)
        R2 = Rf+1.5*0.25*(L-Rf)

    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        setsOfFacesData = []
        setsOfFacesData.append([0.85*R1*np.cos(theta*np.pi/180), 0.85*R1*np.sin(theta*np.pi/180), 0,'MATRIX-EXTANNULUS-CENTERCRACK'])
        setsOfFacesData.append([0.85*R1*np.cos((theta+deltatheta-0.5*deltapsi)*np.pi/180), 0.85*R1*np.sin((theta+deltatheta-0.5*deltapsi)*np.pi/180), 0,'MATRIX-EXTANNULUS-UPPERCRACK-CTUP'])
        setsOfFacesData.append([0.85*R1*np.cos((theta+deltatheta+0.5*deltapsi)*np.pi/180), 0.85*R1*np.sin((theta+deltatheta+0.5*deltapsi)*np.pi/180), 0,'MATRIX-EXTANNULUS-FIRSTBOUNDED-CTUP'])
        setsOfFacesData.append([0.85*R1*np.cos((theta+deltatheta+deltapsi+0.5*deltaphi)*np.pi/180), 0.85*R1*np.sin((theta+deltatheta+deltapsi+0.5*deltaphi)*np.pi/180), 0,'MATRIX-EXTANNULUS-SECONDBOUNDED-CTUP'])
        setsOfFacesData.append([0.85*R1*np.cos((theta-deltatheta+0.5*deltapsi)*np.pi/180), 0.85*R1*np.sin((theta-deltatheta+0.5*deltapsi)*np.pi/180), 0,'MATRIX-EXTANNULUS-UPPERCRACK-CTLOW'])
        setsOfFacesData.append([0.85*R1*np.cos((theta-deltatheta-0.5*deltapsi)*np.pi/180), 0.85*R1*np.sin((theta-deltatheta-0.5*deltapsi)*np.pi/180), 0,'MATRIX-EXTANNULUS-FIRSTBOUNDED-CTLOW'])
        setsOfFacesData.append([0.85*R1*np.cos((theta-deltatheta-deltapsi-0.5*deltaphi)*np.pi/180), 0.85*R1*np.sin((theta-deltatheta-deltapsi-0.5*deltaphi)*np.pi/180), 0,'MATRIX-EXTANNULUS-SECONDBOUNDED-CTLOW'])
        setsOfFacesData.append([0.85*R1*np.cos((theta+deltatheta+deltapsi+deltaphi+1.0)*np.pi/180), 0.85*R1*np.sin((theta+deltatheta+deltapsi+deltaphi+1.0)*np.pi/180), 0,'MATRIX-EXTANNULUS-RESTBOUNDED'])
    else:
        alpha = theta + deltatheta - deltapsi
        beta = theta + deltatheta + deltapsi
        gamma = theta + deltatheta + deltapsi + deltaphi
        setsOfFacesData = [[R1*np.cos(0.5*alpha*np.pi/180), R1*np.sin(0.5*alpha*np.pi/180), 0,'MATRIX-INTANNULUS-LOWERCRACK'],
                           [R1*np.cos((alpha+0.5*deltapsi)*np.pi/180), R1*np.sin((alpha+0.5*deltapsi)*np.pi/180), 0,'MATRIX-INTANNULUS-UPPERCRACK'],
                           [R1*np.cos((theta+deltatheta+0.5*deltapsi)*np.pi/180), R1*np.sin((theta+deltatheta+0.5*deltapsi)*np.pi/180), 0,'MATRIX-INTANNULUS-FIRSTBOUNDED'],
                           [R1*np.cos((beta+0.5*deltaphi)*np.pi/180), R1*np.sin((beta+0.5*deltaphi)*np.pi/180), 0,'MATRIX-INTANNULUS-SECONDBOUNDED'],
                           [R1*np.cos((gamma+0.5*(180-gamma))*np.pi/180), R1*np.sin((gamma+0.5*(180-gamma))*np.pi/180), 0,'MATRIX-INTANNULUS-RESTBOUNDED']]

    for setOfFacesData in setsOfFacesData:
        defineSetOfFacesByFindAt(RVEpart,setOfFacesData[0],setOfFacesData[1],setOfFacesData[2],setOfFacesData[-1],logfilepath,baselogindent + 4*logindent,True)

    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        RVEpart.SetByBoolean(name='MATRIX-EXTANNULUS', sets=[RVEpart.sets['MATRIX-EXTANNULUS-CENTERCRACK'],RVEpart.sets['MATRIX-EXTANNULUS-UPPERCRACK-CTUP'],RVEpart.sets['MATRIX-EXTANNULUS-FIRSTBOUNDED-CTUP'],RVEpart.sets['MATRIX-EXTANNULUS-SECONDBOUNDED-CTUP'],RVEpart.sets['MATRIX-EXTANNULUS-UPPERCRACK-CTLOW'],RVEpart.sets['MATRIX-EXTANNULUS-FIRSTBOUNDED-CTLOW'],RVEpart.sets['MATRIX-EXTANNULUS-SECONDBOUNDED-CTLOW'],RVEpart.sets['MATRIX-EXTANNULUS-RESTBOUNDED']])
    else:
        RVEpart.SetByBoolean(name='MATRIX-INTANNULUS', sets=[RVEpart.sets['MATRIX-INTANNULUS-LOWERCRACK'],RVEpart.sets['MATRIX-INTANNULUS-UPPERCRACK'],RVEpart.sets['MATRIX-INTANNULUS-FIRSTBOUNDED'],RVEpart.sets['MATRIX-INTANNULUS-SECONDBOUNDED'],RVEpart.sets['MATRIX-INTANNULUS-RESTBOUNDED']])
    writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- MATRIX-INTANNULUS',True)

    setsOfFacesData = [[0.0, R2, 0,'MATRIX-INTERMEDIATEANNULUS'],
                       [0.975*L, 0.975*L, 0,'MATRIX-BODY']]

    for setOfFacesData in setsOfFacesData:
        defineSetOfFacesByFindAt(RVEpart,setOfFacesData[0],setOfFacesData[1],setOfFacesData[2],setOfFacesData[-1],logfilepath,baselogindent + 4*logindent,True)

    RVEpart.SetByBoolean(name='MATRIX', sets=[RVEpart.sets['MATRIX-BODY'],RVEpart.sets['MATRIX-INTERMEDIATEANNULUS'],RVEpart.sets['MATRIX-INTANNULUS']])
    writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- MATRIX',True)

    if 'boundingPly' in parameters['BC']['northSide']['type']:
        if 'adjacentFibers' in parameters['BC']['northSide']['type']:
            setsOfFacesData = [[0.975*L, 0.975*(L+Lply+Ludply), 0,'BOUNDING-PLY']]
        else:
            setsOfFacesData = [[0.975*L, 0.975*(L+Lply), 0,'BOUNDING-PLY']]
        for setOfFacesData in setsOfFacesData:
            defineSetOfFacesByFindAt(RVEpart,setOfFacesData[0],setOfFacesData[1],setOfFacesData[2],setOfFacesData[-1],logfilepath,baselogindent + 4*logindent,True)

    if 'boundingPly' in parameters['BC']['rightSide']['type'] and 'boundingPly' in parameters['BC']['leftSide']['type']:
        setsOfFacesData = [[0.975*CornerBx, 0.5*L, 0,'RIGHT-HOMOGENIZED-CROSSPLY'],
                           [0.975*CornerAx, 0.5*L, 0,'LEFT-HOMOGENIZED-CROSSPLY']]
        for setOfFacesData in setsOfFacesData:
            defineSetOfFacesByFindAt(RVEpart,setOfFacesData[0],setOfFacesData[1],setOfFacesData[2],setOfFacesData[-1],logfilepath,baselogindent + 4*logindent,True)
        RVEpart.SetByBoolean(name='HOMOGENIZED-CROSSPLY', sets=[RVEpart.sets['RIGHT-HOMOGENIZED-CROSSPLY'],RVEpart.sets['LEFT-HOMOGENIZED-CROSSPLY']])
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- HOMOGENIZED-CROSSPLY',True)
    elif 'boundingPly' in parameters['BC']['rightSide']['type']:
        setsOfFacesData = [[0.975*CornerBx, 0.5*L, 0,'RIGHT-HOMOGENIZED-CROSSPLY']]
        for setOfFacesData in setsOfFacesData:
            defineSetOfFacesByFindAt(RVEpart,setOfFacesData[0],setOfFacesData[1],setOfFacesData[2],setOfFacesData[-1],logfilepath,baselogindent + 4*logindent,True)
    elif 'boundingPly' in parameters['BC']['leftSide']['type']:
        setsOfFacesData = [[0.975*CornerAx, 0.5*L, 0,'LEFT-HOMOGENIZED-CROSSPLY']]
        for setOfFacesData in setsOfFacesData:
            defineSetOfFacesByFindAt(RVEpart,setOfFacesData[0],setOfFacesData[1],setOfFacesData[2],setOfFacesData[-1],logfilepath,baselogindent + 4*logindent,True)

    setsOfFacesData = []
    booleanSets = []
    if 'adjacentFibers' in parameters['BC']['northSide']['type']:
        for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
            setsOfFacesData.append([0.0, (nFiber+1)*2*L, 0.0,'UPPER-FIBER-C'+str(nFiber+1)])
        if 'adjacentFibers' in parameters['BC']['rightSide']['type']:
            for mFiber in range(0,parameters['BC']['rightSide']['nFibers']):
                for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
                    setsOfFacesData.append([(mFiber+1)*2*L, (nFiber+1)*2*L, 0.0,'UPPER-FIBER-R'+str(int(nFiber+1+mFiber*parameters['BC']['northSide']['nFibers']))])
        if 'adjacentFibers' in parameters['BC']['leftSide']['type']:
            for mFiber in range(0,parameters['BC']['leftSide']['nFibers']):
                for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
                    setsOfFacesData.append([-(mFiber+1)*2*L, (nFiber+1)*2*L, 0.0,'UPPER-FIBER-L'+str(int(nFiber+1+mFiber*parameters['BC']['northSide']['nFibers']))])
        for setOfFacesData in setsOfFacesData:
            defineSetOfFacesByFindAt(RVEpart,setOfFacesData[0],setOfFacesData[1],setOfFacesData[2],setOfFacesData[-1],logfilepath,baselogindent + 4*logindent,True)
            booleanSets.append(RVEpart.sets[setOfFacesData[-1]])
        RVEpart.SetByBoolean(name='UPPER-FIBERS', sets=booleanSets)

    setsOfFacesData = []
    booleanSets = []
    if 'adjacentFibers' in parameters['BC']['rightSide']['type']:
        for nFiber in range(0,parameters['BC']['rightSide']['nFibers']):
            setsOfFacesData.append([(nFiber+1)*2*L, 0.25*Rf, 0.0,'RIGHT-FIBER'+str(nFiber+1)])
        for setOfFacesData in setsOfFacesData:
            defineSetOfFacesByFindAt(RVEpart,setOfFacesData[0],setOfFacesData[1],setOfFacesData[2],setOfFacesData[-1],logfilepath,baselogindent + 4*logindent,True)
            booleanSets.append(RVEpart.sets[setOfFacesData[-1]])
        RVEpart.SetByBoolean(name='RIGHT-FIBERS', sets=booleanSets)

    setsOfFacesData = []
    booleanSets = []
    if 'adjacentFibers' in parameters['BC']['leftSide']['type']:
        for nFiber in range(0,parameters['BC']['rightSide']['nFibers']):
            setsOfFacesData.append([-(nFiber+1)*2*L, 0.25*Rf, 0.0,'LEFT-FIBER'+str(nFiber+1)])
        for setOfFacesData in setsOfFacesData:
            defineSetOfFacesByFindAt(RVEpart,setOfFacesData[0],setOfFacesData[1],setOfFacesData[2],setOfFacesData[-1],logfilepath,baselogindent + 4*logindent,True)
            booleanSets.append(RVEpart.sets[setOfFacesData[-1]])
        RVEpart.SetByBoolean(name='LEFT-FIBERS', sets=booleanSets)

    booleanSets = [RVEpart.sets['FIBER'],RVEpart.sets['MATRIX']]
    if 'boundingPly' in parameters['BC']['northSide']['type']:
        booleanSets.append(RVEpart.sets['BOUNDING-PLY'])
    if 'boundingPly' in parameters['BC']['rightSide']['type']:
        booleanSets.append(RVEpart.sets['RIGHT-HOMOGENIZED-CROSSPLY'])
    if 'boundingPly' in parameters['BC']['leftSide']['type']:
        booleanSets.append(RVEpart.sets['LEFT-HOMOGENIZED-CROSSPLY'])
    if 'adjacentFibers' in parameters['BC']['northSide']['type']:
        booleanSets.append(RVEpart.sets['UPPER-FIBERS'])
    if 'adjacentFibers' in parameters['BC']['rightSide']['type']:
        booleanSets.append(RVEpart.sets['RIGHT-FIBERS'])
    if 'adjacentFibers' in parameters['BC']['leftSide']['type']:
        booleanSets.append(RVEpart.sets['LEFT-FIBERS'])

    RVEpart.SetByBoolean(name='RVE', sets=booleanSets)
    writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- RVE',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    # sets of cells (none, i.e. 2D geometry)

    mdb.save()

    writeLineToLogFile(logfilepath,'a',2*logindent + '... done.',True)

    #===============================================================================#
    #                             Material Orientation
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Creating reference system for material orientation ...',True)
    RVEpart.DatumCsysByThreePoints(name='refOrientation',coordSysType=CARTESIAN,origin=(0.0,0.0,0.0),point1=(1.0,0.0,0.0),point2=(1.0,1.0,0.0))
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Assigning material orientation to FIBER ...',True)
    RVEpart.MaterialOrientation(orientationType=SYSTEM,region=RVEpart.sets['FIBER'],localCsys=RVEpart.datums[RVEpart.features['refOrientation'].id])
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Assigning material orientation to MATRIX ...',True)
    RVEpart.MaterialOrientation(orientationType=SYSTEM,region=RVEpart.sets['MATRIX'],localCsys=RVEpart.datums[RVEpart.features['refOrientation'].id])
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

    if 'boundingPly' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Assigning material orientation to BOUNDING-PLY ...',True)
        RVEpart.MaterialOrientation(orientationType=SYSTEM,region=RVEpart.sets['BOUNDING-PLY'],localCsys=RVEpart.datums[RVEpart.features['refOrientation'].id])
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

    if 'boundingPly' in parameters['BC']['rightSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Assigning material orientation to RIGHT-HOMOGENIZED-CROSSPLY ...',True)
        RVEpart.MaterialOrientation(orientationType=SYSTEM,region=RVEpart.sets['RIGHT-HOMOGENIZED-CROSSPLY'],localCsys=RVEpart.datums[RVEpart.features['refOrientation'].id])
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

    if 'boundingPly' in parameters['BC']['leftSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Assigning material orientation to LEFT-HOMOGENIZED-CROSSPLY ...',True)
        RVEpart.MaterialOrientation(orientationType=SYSTEM,region=RVEpart.sets['LEFT-HOMOGENIZED-CROSSPLY'],localCsys=RVEpart.datums[RVEpart.features['refOrientation'].id])
        writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)


    #===============================================================================#
    #                             Materials creation
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Creating materials ...',True)

    for material in parameters['materials'].values():
        mdb.models[modelname].Material(name=material['name'])
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'MATERIAL: ' + material['name'],True)
        try:
            values = material['elastic']['values']
            tuplelist = []
            valuelist = []
            for v,value in enumerate(values):
                valuelist.append(value)
            tuplelist.append(tuple(valuelist))
            mdb.models[modelname].materials[material['name']].Elastic(type=material['elastic']['type'],table=tuple(tuplelist))
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  ELASTIC',True)
            line = '    '
            for v,value in enumerate(values):
                if v>0:
                    line += ', '
                line += str(value)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + line,True)
        except Exception, error:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  NO ELASTIC PROPERTY',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + str(Exception),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + str(error),True)
            #sys.exit(2)
            sys.exc_clear()
        try:
            values = material['density']['values']
            tuplelist = []
            valuelist = []
            for v,value in enumerate(values):
                valuelist.append(value)
            tuplelist.append(tuple(valuelist))
            mdb.models[modelname].materials[material['name']].Density(table=tuple(tuplelist))
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  DENSITY',True)
            line = '    '
            for v,value in enumerate(values):
                if v>0:
                    line += ', '
                line += str(value)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + line,True)
        except Exception, error:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  NO DENSITY PROPERTY',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + str(Exception),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + str(error),True)
            sys.exc_clear()
        try:
            values = material['thermalexpansion']['values']
            tuplelist = []
            valuelist = []
            for v,value in enumerate(values):
                valuelist.append(value)
            tuplelist.append(tuple(valuelist))
            mdb.models[modelname].materials[material['name']].Expansion(type=material['thermalexpansion']['type'],table=tuple(tuplelist))
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  THERMAL EXPANSION',True)
            line = '    '
            for v,value in enumerate(values):
                if v>0:
                    line += ', '
                line += str(value)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + line,True)
        except Exception, error:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  NO THERMAL EXPANSION PROPERTY',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + str(Exception),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + str(error),True)
            sys.exc_clear()
        try:
            values = material['thermalconductivity']['values']
            tuplelist = []
            valuelist = []
            for v,value in enumerate(values):
                valuelist.append(value)
            tuplelist.append(tuple(valuelist))
            mdb.models[modelname].materials[material['name']].Conductivity(type=material['thermalconductivity']['type'],table=tuple(tuplelist))
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  THERMAL CONDUCTIVITY',True)
            line = '    '
            for v,value in enumerate(values):
                if v>0:
                    line += ', '
                line += str(value)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + line,True)
        except Exception, error:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  NO THERMAL CONDUCTIVITY PROPERTY',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + str(Exception),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + str(error),True)
            sys.exc_clear()

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #===============================================================================#
    #                             Sections creation
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Creating sections ...',True)

    for section in parameters['sections'].values():
        if 'HomogeneousSolidSection' in section['type'] or 'Homogeneous Solid Section' in section['type'] or 'homogeneoussolidsection' in section['type'] or 'homogeneous solid section' in section['type'] or 'Homogeneous solid section' in section['type']:
            mdb.models[modelname].HomogeneousSolidSection(name=section['name'],
            material=section['material'], thickness=section['thickness'])

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #===============================================================================#
    #                             Sections assignment
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Making section assignments ...',True)

    for sectionRegion in parameters['sectionRegions'].values():
        RVEpart.SectionAssignment(region=RVEpart.sets[sectionRegion['set']], sectionName=sectionRegion['name'], offset=sectionRegion['offsetValue'],offsetType=sectionRegion['offsetType'], offsetField=sectionRegion['offsetField'],thicknessAssignment=sectionRegion['thicknessAssignment'])

    # p.SectionAssignment(region=region, sectionName='MatrixSection', offset=0.0,
    #     offsetType=MIDDLE_SURFACE, offsetField='',
    #     thicknessAssignment=FROM_SECTION)

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #===============================================================================#
    #                             Instance creation
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Creating instance ...',True)

    model.rootAssembly.DatumCsysByDefault(CARTESIAN)
    model.rootAssembly.Instance(name='RVE-assembly', part=RVEpart, dependent=OFF)

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #===============================================================================#
    #                             Step creation
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Creating step ...',True)

    for step in parameters['steps'].values():
        model.StaticStep(name=step['name'], previous=step['previous'],minInc=step['minimumIncrement'])

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #===============================================================================#
    #                             Boundary conditions
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Assigning boundary conditions ...',True)

    # SOUTH side: symmetry line

    if 'full' in parameters['geometry']['fiber']['type']:
        for step in parameters['steps'].values():
            if 'symmetric' in parameters['BC']['northSide']['type']:
                model.YsymmBC(name='NorthSymmetryBound', createStepName=step['name'],region=model.rootAssembly.instances['RVE-assembly'].sets['UPPERSIDE'], localCsys=None)
            if 'symmetric' in parameters['BC']['southSide']['type']:
                model.YsymmBC(name='SouthSymmetryBound', createStepName=step['name'],region=model.rootAssembly.instances['RVE-assembly'].sets['LOWERSIDE'], localCsys=None)
            if 'symmetric' in parameters['BC']['rightSide']['type']:
                model.XsymmBC(name='RightSymmetryBound', createStepName=step['name'],region=model.rootAssembly.instances['RVE-assembly'].sets['RIGHTSIDE'], localCsys=None)
            if 'symmetric' in parameters['BC']['leftSide']['type']:
                model.XsymmBC(name='LeftSymmetryBound', createStepName=step['name'],region=model.rootAssembly.instances['RVE-assembly'].sets['LEFTSIDE'], localCsys=None)
    elif 'half' in parameters['geometry']['fiber']['type']:
        for step in parameters['steps'].values():
            model.YsymmBC(name='SymmetryBound', createStepName=step['name'],region=model.rootAssembly.instances['RVE-assembly'].sets['LOWERSIDE'], localCsys=None)
            if 'symmetric' in parameters['BC']['rightSide']['type']:
                model.XsymmBC(name='RightSymmetryBound', createStepName=step['name'],region=model.rootAssembly.instances['RVE-assembly'].sets['RIGHTSIDE'], localCsys=None)
            if 'symmetric' in parameters['BC']['leftSide']['type']:
                model.XsymmBC(name='LeftSymmetryBound', createStepName=step['name'],region=model.rootAssembly.instances['RVE-assembly'].sets['LEFTSIDE'], localCsys=None)
    elif 'quarter' in parameters['geometry']['fiber']['type']:
        for step in parameters['steps'].values():
            model.YsymmBC(name='LowerSymmetryBound', createStepName=step['name'],region=model.rootAssembly.instances['RVE-assembly'].sets['LOWERSIDE'], localCsys=None)
            model.XsymmBC(name='LeftSymmetryBound', createStepName=step['name'],region=model.rootAssembly.instances['RVE-assembly'].sets['LEFTSIDE'], localCsys=None)
    else:
        for step in parameters['steps'].values():
            model.YsymmBC(name='SymmetryBound', createStepName=step['name'],region=model.rootAssembly.instances['RVE-assembly'].sets['LOWERSIDE'], localCsys=None)

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #===============================================================================#
    #                                Applied load
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',2*logindent + 'Assigning loads ...',True)

    for load in parameters['loads'].values():
        writeLineToLogFile(logfilepath,'a',3*logindent + 'Apply ' + load['type'] + ' on ' + load['set'] + ' set',True)
        if 'appliedstrain' in load['type'] or 'appliedStrain' in load['type'] or 'Applied Strain' in load['type'] or 'applied strain' in load['type']:
            if 'right' in load['set'] or 'Right' in load['set'] or 'RIGHT' in load['set']:
                model.DisplacementBC(name=load['name'],createStepName=load['stepName'],region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], u1=load['value'][0]*CornerBx, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',localCsys=None)
            elif 'left' in load['set'] or 'Left' in load['set'] or 'LEFT' in load['set']:
                model.DisplacementBC(name=load['name'],createStepName=load['stepName'],region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], u1=load['value'][0]*CornerAx, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',localCsys=None)
            elif 'upper' in load['set'] or 'Upper' in load['set'] or 'UPPER' in load['set']:
                model.DisplacementBC(name=load['name'],createStepName=load['stepName'],region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], u2=load['value'][1]*CornerBy, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',localCsys=None)
        elif 'applieddisplacement' in load['type'] or 'appliedDisplacement' in load['type'] or 'Applied Displacement' in load['type'] or 'applied displacement' in load['type']:
            model.DisplacementBC(name=load['name'],createStepName=load['stepName'],region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], u1=load['value'][0], amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',localCsys=None)
        elif 'temperature' in load['type'] or 'Temperature' in load['type'] or 'TEMPERATURE' in load['type']:
            model.TemperatureBC(name=load['name'],createStepName=load['stepName'],region=model.rootAssembly.instances['RVE-assembly'].sets[load['set']], magnitude=load['value'],distributionType=UNIFORM)
        # elif 'appliedstress' in load['type'] or 'appliedStress' in load['type'] or 'Applied Stress' in load['type'] or 'applied stress' in load['type']:
        #
        # elif 'appliedforce' in load['type'] or 'appliedForce' in load['type'] or 'Applied Force' in load['type'] or 'applied Force' in load['type']:

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #===============================================================================#
    #                                   Crack
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Creating cracks ...',True)

    # assign seam
    model.rootAssembly.engineeringFeatures.assignSeam(regions=model.rootAssembly.instances['RVE-assembly'].sets['CRACK'])

    if 'inverseSquareRoot' in parameters['singularity']['type']:
        midNodePos = 0.25
    else:
        midNodePos = 0.5

    # contour integral
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
      xC = Rf*np.cos((theta+deltatheta)*np.pi/180)
      yC = Rf*np.sin((theta+deltatheta)*np.pi/180)
      xA = Rf*np.cos((theta+1.025*deltatheta)*np.pi/180)
      yA = -xC*(xA-xC)/yC + yC
      model.rootAssembly.engineeringFeatures.ContourIntegral(name='DebondUp',symmetric=OFF,crackFront=model.rootAssembly.instances['RVE-assembly'].sets['CRACK'],crackTip=model.rootAssembly.instances['RVE-assembly'].sets['CRACKTIPUP'],extensionDirectionMethod=Q_VECTORS, qVectors=(((xC,yC,0.0),(xA,yA,0.0)), ), midNodePosition=midNodePos, collapsedElementAtTip=NONE)
      xC = Rf*np.cos((theta-deltatheta)*np.pi/180)
      yC = Rf*np.sin((theta-deltatheta)*np.pi/180)
      xA = Rf*np.cos((theta-1.025*deltatheta)*np.pi/180)
      yA = -xC*(xA-xC)/yC + yC
      model.rootAssembly.engineeringFeatures.ContourIntegral(name='DebondLow',symmetric=OFF,crackFront=model.rootAssembly.instances['RVE-assembly'].sets['CRACK'],crackTip=model.rootAssembly.instances['RVE-assembly'].sets['CRACKTIPLOW'],extensionDirectionMethod=Q_VECTORS, qVectors=(((xC,yC,0.0),(xA,yA,0.0)), ), midNodePosition=midNodePos, collapsedElementAtTip=NONE)
    else:
      xC = Rf*np.cos((theta+deltatheta)*np.pi/180)
      yC = Rf*np.sin((theta+deltatheta)*np.pi/180)
      xA = Rf*np.cos((theta+1.025*deltatheta)*np.pi/180)
      yA = -xC*(xA-xC)/yC + yC
      model.rootAssembly.engineeringFeatures.ContourIntegral(name='Debond',symmetric=OFF,crackFront=model.rootAssembly.instances['RVE-assembly'].sets['CRACK'],crackTip=model.rootAssembly.instances['RVE-assembly'].sets['CRACKTIP'],extensionDirectionMethod=Q_VECTORS, qVectors=(((xC,yC,0.0),(xA,yA,0.0)), ), midNodePosition=midNodePos, collapsedElementAtTip=NONE)

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #===============================================================================#
    #                                   Mesh
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Creating mesh ...',True)

    nTangential = np.floor(deltapsi/delta)
    nRadialFiber = np.floor(0.25/(delta*np.pi/180.0))
    nTangential1 = np.floor(deltaphi/parameters['mesh']['size']['delta2'])
    nTangential2 = np.floor((180-(theta+deltatheta+deltapsi+deltaphi))/parameters['mesh']['size']['delta3'])
    nTangential3 = np.floor(alpha/parameters['mesh']['size']['delta1'])
    #nRadialFiber1 = np.floor(0.25/parameters['mesh']['size']['delta3'])
    if L>2*Rf:
        nRadialMatrix = np.floor(0.25/(delta*np.pi/180.0))
        #nRadialMatrix1 = np.floor(0.25/parameters['mesh']['size']['delta3'])
    else:
        nRadialMatrix = np.floor(0.25*(L-Rf)/(delta*np.pi/180.0))
        #nRadialMatrix1 = np.floor(0.25*(L-Rf)/(Rf*parameters['mesh']['size']['delta3']))

    if nTangential<parameters['Jintegral']['numberOfContours'] or nRadialFiber<parameters['Jintegral']['numberOfContours'] or nRadialMatrix<parameters['Jintegral']['numberOfContours']:
        parameters['Jintegral']['numberOfContours'] = int(np.floor(np.min([nTangential,nRadialFiber,nRadialMatrix])) - 1)
        writeErrorToLogFile(logfilepath,'a','MESH SIZE','The provided element size around the crack tip is incompatible with the number of contour integral requested.\nContour integral option in ABAQUS is available only for quadrilateral and hexahedral elements.\nThe number of contour requested will be automatically adjusted to ' + str(parameters['Jintegral']['numberOfContours']),True)

    # assign mesh controls
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Assigning mesh controls ...',True)

    regionSets = [['FIBER-CENTER',QUAD_DOMINATED,FREE],
                  ['FIBER-INTERMEDIATEANNULUS',QUAD_DOMINATED,FREE],
                  ['FIBER-EXTANNULUS-RESTBOUNDED',QUAD_DOMINATED,FREE],
                  ['MATRIX-INTANNULUS-RESTBOUNDED',TRI,FREE],
                  ['MATRIX-INTERMEDIATEANNULUS',TRI,FREE],
                  ['MATRIX-BODY',QUAD_DOMINATED,FREE]]
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        regionSets.append(['FIBER-EXTANNULUS-CRACK',QUAD_DOMINATED,FREE])
        regionSets.append(['FIBER-EXTANNULUS-UPPERCRACK-CTUP',QUAD,STRUCTURED])
        regionSets.append(['FIBER-EXTANNULUS-FIRSTBOUNDED-CTUP',QUAD,STRUCTURED])
        regionSets.append(['FIBER-EXTANNULUS-SECONDBOUNDED-CTUP',QUAD_DOMINATED,FREE])
        regionSets.append(['FIBER-EXTANNULUS-UPPERCRACK-CTLOW',QUAD,STRUCTURED])
        regionSets.append(['FIBER-EXTANNULUS-FIRSTBOUNDED-CTLOW',QUAD,STRUCTURED])
        regionSets.append(['FIBER-EXTANNULUS-SECONDBOUNDED-CTLOW',QUAD_DOMINATED,FREE])
        regionSets.append(['MATRIX-INTANNULUS-CRACK',QUAD_DOMINATED,FREE])
        regionSets.append(['MATRIX-INTANNULUS-UPPERCRACK-CTUP',QUAD,STRUCTURED])
        regionSets.append(['MATRIX-INTANNULUS-FIRSTBOUNDED-CTUP',QUAD,STRUCTURED])
        regionSets.append(['MATRIX-INTANNULUS-SECONDBOUNDED-CTUP',TRI,FREE])
        regionSets.append(['MATRIX-INTANNULUS-UPPERCRACK-CTLOW',QUAD,STRUCTURED])
        regionSets.append(['MATRIX-INTANNULUS-FIRSTBOUNDED-CTLOW',QUAD,STRUCTURED])
        regionSets.append(['MATRIX-INTANNULUS-SECONDBOUNDED-CTLOW',TRI,FREE])
    else:
        regionSets.append(['FIBER-EXTANNULUS-LOWERCRACK',QUAD_DOMINATED,FREE])
        regionSets.append(['FIBER-EXTANNULUS-UPPERCRACK',QUAD,STRUCTURED])
        regionSets.append(['FIBER-EXTANNULUS-FIRSTBOUNDED',QUAD,STRUCTURED])
        regionSets.append(['FIBER-EXTANNULUS-SECONDBOUNDED',QUAD_DOMINATED,FREE])
        regionSets.append(['MATRIX-INTANNULUS-LOWERCRACK',QUAD_DOMINATED,FREE])
        regionSets.append(['MATRIX-INTANNULUS-UPPERCRACK',QUAD,STRUCTURED])
        regionSets.append(['MATRIX-INTANNULUS-FIRSTBOUNDED',QUAD,STRUCTURED])
        regionSets.append(['MATRIX-INTANNULUS-SECONDBOUNDED',TRI,FREE])

    if 'boundingPly' in parameters['BC']['northSide']['type']:
        regionSets.append(['BOUNDING-PLY',QUAD_DOMINATED,FREE])
    if 'boundingPly' in parameters['BC']['rightSide']['type']:
        regionSets.append(['RIGHT-HOMOGENIZED-CROSSPLY',QUAD_DOMINATED,FREE])
    if 'boundingPly' in parameters['BC']['leftSide']['type']:
        regionSets.append(['LEFT-HOMOGENIZED-CROSSPLY',QUAD_DOMINATED,FREE])
    if 'adjacentFibers' in parameters['BC']['northSide']['type']:
        regionSets.append(['UPPER-FIBERS',QUAD_DOMINATED,FREE])
    if 'adjacentFibers' in parameters['BC']['rightSide']['type']:
        regionSets.append(['RIGHT-FIBERS',QUAD_DOMINATED,FREE])
    if 'adjacentFibers' in parameters['BC']['leftSide']['type']:
        regionSets.append(['LEFT-FIBERS',QUAD_DOMINATED,FREE])

    for regionSet in regionSets:
        assignMeshControls(model,'RVE-assembly',regionSet[0],regionSet[1],regionSet[2],logfilepath,baselogindent + 3*logindent,True)

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    # assign seeds
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Seeding edges ...',True)

    regionSets = [['FIRSTCIRCLE',18],
                  ['FIFTHCIRCLE',90]]
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        regionSets.append(['SECONDCIRCLE-UPPERCRACK-CTUP',nTangential])
        regionSets.append(['SECONDCIRCLE-FIRSTBOUNDED-CTUP',nTangential])
        regionSets.append(['THIRDCIRCLE-UPPERCRACK-CTUP',nTangential])
        regionSets.append(['THIRDCIRCLE-FIRSTBOUNDED-CTUP',nTangential])
        regionSets.append(['FOURTHCIRCLE-UPPERCRACK-CTUP',nTangential])
        regionSets.append(['FOURTHCIRCLE-FIRSTBOUNDED-CTUP',nTangential])
        regionSets.append(['SECONDCIRCLE-UPPERCRACK-CTLOW',nTangential])
        regionSets.append(['SECONDCIRCLE-FIRSTBOUNDED-CTLOW',nTangential])
        regionSets.append(['THIRDCIRCLE-UPPERCRACK-CTLOW',nTangential])
        regionSets.append(['THIRDCIRCLE-FIRSTBOUNDED-CTLOW',nTangential])
        regionSets.append(['FOURTHCIRCLE-UPPERCRACK-CTLOW',nTangential])
        regionSets.append(['FOURTHCIRCLE-FIRSTBOUNDED-CTLOW',nTangential])
        regionSets.append(['TRANSVERSALCUT-FIRSTFIBER-CTUP',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-FIRSTMATRIX-CTUP',nRadialMatrix])
        regionSets.append(['TRANSVERSALCUT-SECONDFIBER-CTUP',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-SECONDMATRIX-CTUP',nRadialMatrix])
        regionSets.append(['TRANSVERSALCUT-THIRDFIBER-CTUP',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-THIRDMATRIX-CTUP',nRadialMatrix])
        regionSets.append(['TRANSVERSALCUT-FIRSTFIBER-CTLOW',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-FIRSTMATRIX-CTLOW',nRadialMatrix])
        regionSets.append(['TRANSVERSALCUT-SECONDFIBER-CTLOW',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-SECONDMATRIX-CTLOW',nRadialMatrix])
        regionSets.append(['TRANSVERSALCUT-THIRDFIBER-CTLOW',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-THIRDMATRIX-CTLOW',nRadialMatrix])
        regionSets.append(['SECONDCIRCLE-SECONDBOUNDED-CTUP',nTangential1])
        regionSets.append(['SECONDCIRCLE-SECONDBOUNDED-CTLOW',nTangential1])
        regionSets.append(['SECONDCIRCLE-RESTBOUNDED',nTangential2])
        regionSets.append(['THIRDCIRCLE-SECONDBOUNDED-CTUP',nTangential1])
        regionSets.append(['THIRDCIRCLE-SECONDBOUNDED-CTLOW',nTangential1])
        regionSets.append(['THIRDCIRCLE-RESTBOUNDED',nTangential2])
        regionSets.append(['FOURTHCIRCLE-SECONDBOUNDED-CTUP',nTangential1])
        regionSets.append(['FOURTHCIRCLE-SECONDBOUNDED-CTLOW',nTangential1])
        regionSets.append(['FOURTHCIRCLE-RESTBOUNDED',nTangential2])
        regionSets.append(['TRANSVERSALCUT-FOURTHFIBER-CTUP',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-FOURTHMATRIX-CTUP',nRadialMatrix])
        regionSets.append(['TRANSVERSALCUT-FOURTHFIBER-CTLOW',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-FOURTHMATRIX-CTLOW',nRadialMatrix])
        regionSets.append(['SECONDCIRCLE-CRACK',nTangential3])
        regionSets.append(['THIRDCIRCLE-CRACK',nTangential3])
        regionSets.append(['FOURTHCIRCLE-CRACK',nTangential3])
        if 'full' not in parameters['geometry']['fiber']['type']:
            regionSets.append(['LOWERSIDE-CENTER',6])
            regionSets.append(['LOWERSIDE-SECONDRING-RIGHT',nRadialFiber])
            regionSets.append(['LOWERSIDE-THIRDRING-RIGHT',nRadialMatrix])
    else:
        regionSets.append(['SECONDCIRCLE-UPPERCRACK',nTangential])
        regionSets.append(['SECONDCIRCLE-FIRSTBOUNDED',nTangential])
        regionSets.append(['THIRDCIRCLE-UPPERCRACK',nTangential])
        regionSets.append(['THIRDCIRCLE-FIRSTBOUNDED',nTangential])
        regionSets.append(['FOURTHCIRCLE-UPPERCRACK',nTangential])
        regionSets.append(['FOURTHCIRCLE-FIRSTBOUNDED',nTangential])
        regionSets.append(['TRANSVERSALCUT-FIRSTFIBER',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-FIRSTMATRIX',nRadialMatrix])
        regionSets.append(['TRANSVERSALCUT-SECONDFIBER',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-SECONDMATRIX',nRadialMatrix])
        regionSets.append(['TRANSVERSALCUT-THIRDFIBER',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-THIRDMATRIX',nRadialMatrix])
        regionSets.append(['LOWERSIDE-SECONDRING-RIGHT',nRadialFiber])
        regionSets.append(['LOWERSIDE-THIRDRING-RIGHT',nRadialMatrix])
        regionSets.append(['SECONDCIRCLE-SECONDBOUNDED',nTangential1])
        regionSets.append(['SECONDCIRCLE-RESTBOUNDED',nTangential2])
        regionSets.append(['THIRDCIRCLE-SECONDBOUNDED',nTangential1])
        regionSets.append(['THIRDCIRCLE-RESTBOUNDED',nTangential2])
        regionSets.append(['FOURTHCIRCLE-SECONDBOUNDED',nTangential1])
        regionSets.append(['FOURTHCIRCLE-RESTBOUNDED',nTangential2])
        regionSets.append(['TRANSVERSALCUT-FOURTHFIBER',nRadialFiber])
        regionSets.append(['TRANSVERSALCUT-FOURTHMATRIX',nRadialMatrix])
        regionSets.append(['SECONDCIRCLE-LOWERCRACK',nTangential3])
        regionSets.append(['THIRDCIRCLE-LOWERCRACK',nTangential3])
        regionSets.append(['FOURTHCIRCLE-LOWERCRACK',nTangential3])

    nFibersHorizontal = 1

    if 'adjacentFibers' in parameters['BC']['rightSide']['type']:
        nFibersHorizontal += parameters['BC']['rightSide']['nFibers']
        for nFiber in range(0,parameters['BC']['rightSide']['nFibers']):
            regionSets.append(['LOWERSIDE-RIGHT-FIBER'+str(nFiber+1),10])

    if 'adjacentFibers' in parameters['BC']['leftSide']['type']:
        nFibersHorizontal += parameters['BC']['leftSide']['nFibers']
        for nFiber in range(0,parameters['BC']['leftSide']['nFibers']):
            regionSets.append(['LOWERSIDE-LEFT-FIBER'+str(nFiber+1),10])

    regionSets.append(['UPPERSIDE',30*nFibersHorizontal])

    if 'boundingPly' in parameters['BC']['northSide']['type']:
        if 'adjacentFibers' in parameters['BC']['northSide']['type'] and parameters['BC']['northSide']['nFibers']>10:
            regionSets.append(['RIGHTSIDE',int(np.floor(30*(1+10*math.log10(parameters['BC']['northSide']['nFibers']))))])
            regionSets.append(['LEFTSIDE',int(np.floor(30*(1+10*math.log10(parameters['BC']['northSide']['nFibers']))))])
        elif 'adjacentFibers' in parameters['BC']['northSide']['type'] and 'adjacentFibers' in parameters['BC']['rightSide']['type'] and 'adjacentFibers' in parameters['BC']['leftSide']['type'] and parameters['BC']['rightSide']['nFibers']>10 and parameters['BC']['leftSide']['nFibers']>10:
            regionSets.append(['RIGHTSIDE',int(np.floor(30*(1+5*math.log10(parameters['BC']['northSide']['nFibers']))))])
            regionSets.append(['LEFTSIDE',int(np.floor(30*(1+5*math.log10(parameters['BC']['northSide']['nFibers']))))])
        else:
            regionSets.append(['LOWER-RIGHTSIDE',30])
            regionSets.append(['LOWER-LEFTSIDE',30])
        regionSets.append(['UPPER-RIGHTSIDE',int(np.floor(30*(1+math.log10(tRatio))))])
        regionSets.append(['UPPER-LEFTSIDE',int(np.floor(30*(1+math.log10(tRatio))))])
    elif 'adjacentFibers' in parameters['BC']['northSide']['type'] and parameters['BC']['northSide']['nFibers']>10:
        regionSets.append(['RIGHTSIDE',int(np.floor(30*(1+10*math.log10(parameters['BC']['northSide']['nFibers']))))])
        regionSets.append(['LEFTSIDE',int(np.floor(30*(1+10*math.log10(parameters['BC']['northSide']['nFibers']))))])
    elif 'adjacentFibers' in parameters['BC']['northSide']['type'] and 'adjacentFibers' in parameters['BC']['rightSide']['type'] and 'adjacentFibers' in parameters['BC']['leftSide']['type'] and parameters['BC']['rightSide']['nFibers']>10 and parameters['BC']['leftSide']['nFibers']>10:
        regionSets.append(['RIGHTSIDE',int(np.floor(30*(1+5*math.log10(parameters['BC']['northSide']['nFibers']))))])
        regionSets.append(['LEFTSIDE',int(np.floor(30*(1+5*math.log10(parameters['BC']['northSide']['nFibers']))))])
    else:
        regionSets.append(['RIGHTSIDE',30])
        regionSets.append(['LEFTSIDE',30])

    if 'adjacentFibers' in parameters['BC']['northSide']['type']:
        for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
            regionSets.append(['INTERFACE-UPPER-FIBER-C'+str(nFiber+1),72])
        if 'adjacentFibers' in parameters['BC']['rightSide']['type']:
            for mFiber in range(0,parameters['BC']['rightSide']['nFibers']):
                for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
                    regionSets.append(['INTERFACE-UPPER-FIBER-R'+str(int(nFiber+1+mFiber*parameters['BC']['northSide']['nFibers'])),72])
        if 'adjacentFibers' in parameters['BC']['leftSide']['type']:
            for mFiber in range(0,parameters['BC']['leftSide']['nFibers']):
                for nFiber in range(0,parameters['BC']['northSide']['nFibers']):
                    regionSets.append(['INTERFACE-UPPER-FIBER-L'+str(int(nFiber+1+mFiber*parameters['BC']['northSide']['nFibers'])),72])

    for regionSet in regionSets:
        seedEdgeByNumber(model,'RVE-assembly',regionSet[0],regionSet[1],FINER,logfilepath,baselogindent + 3*logindent,True)

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    # select element type
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Selecting and assigning element types ...',True)

    if 'structuralModel' in parameters['mesh']['elements'].keys():
        if 'generalizedPlaneStrain' in parameters['mesh']['elements']['structuralModel']:
            if 'first' in parameters['mesh']['elements']['order']:
                elemType1 = mesh.ElemType(elemCode=CPEG4, elemLibrary=STANDARD)
                elemType2 = mesh.ElemType(elemCode=CPEG3, elemLibrary=STANDARD)
            elif 'second' in parameters['mesh']['elements']['order']:
                elemType1 = mesh.ElemType(elemCode=CPEG8, elemLibrary=STANDARD)
                elemType2 = mesh.ElemType(elemCode=CPEG6, elemLibrary=STANDARD)
        #elif 'generalizedPlaneStress' in parameters['mesh']['elements']['structuralModel']:
        #    if 'first' in parameters['mesh']['elements']['order']:
        #        elemType1 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
        #        elemType2 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
        #    elif 'second' in parameters['mesh']['elements']['order']:
        #        elemType1 = mesh.ElemType(elemCode=CPE8, elemLibrary=STANDARD)
        #        elemType2 = mesh.ElemType(elemCode=CPE6, elemLibrary=STANDARD)
        elif 'planeStrain' in parameters['mesh']['elements']['structuralModel']:
            if 'first' in parameters['mesh']['elements']['order']:
                elemType1 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
                elemType2 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
            elif 'second' in parameters['mesh']['elements']['order']:
                elemType1 = mesh.ElemType(elemCode=CPE8, elemLibrary=STANDARD)
                elemType2 = mesh.ElemType(elemCode=CPE6, elemLibrary=STANDARD)
        elif 'planeStress' in parameters['mesh']['elements']['structuralModel']:
            if 'first' in parameters['mesh']['elements']['order']:
                elemType1 = mesh.ElemType(elemCode=CPS4, elemLibrary=STANDARD)
                elemType2 = mesh.ElemType(elemCode=CPS3, elemLibrary=STANDARD)
            elif 'second' in parameters['mesh']['elements']['order']:
                elemType1 = mesh.ElemType(elemCode=CPS8, elemLibrary=STANDARD)
                elemType2 = mesh.ElemType(elemCode=CPS6, elemLibrary=STANDARD)
    else:
        if 'first' in parameters['mesh']['elements']['order']:
            elemType1 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
            elemType2 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
        elif 'second' in parameters['mesh']['elements']['order']:
            elemType1 = mesh.ElemType(elemCode=CPE8, elemLibrary=STANDARD)
            elemType2 = mesh.ElemType(elemCode=CPE6, elemLibrary=STANDARD)
    model.rootAssembly.setElementType(regions=(model.rootAssembly.instances['RVE-assembly'].sets['RVE']), elemTypes=(elemType1, elemType2))

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    # mesh part
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Meshing part ...',True)
    localStart = timeit.default_timer()

    model.rootAssembly.generateMesh(regions=(model.rootAssembly.instances['RVE-assembly'],))

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Mesh creation time: ' + str(timeit.default_timer() - localStart) + ' [s]',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    mdb.save()

    # extract mesh statistics
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extracting mesh statistics ...',True)

    meshStats = model.rootAssembly.getMeshStats(regions=(model.rootAssembly.instances['RVE-assembly'],))

    modelData = {}
    modelData['numNodes'] =  meshStats.numNodes
    modelData['numQuads'] =  meshStats.numQuadElems
    modelData['numTris'] =  meshStats.numTriElems
    modelData['numEls'] =  meshStats.numQuadElems + meshStats.numTriElems

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #===============================================================================#
    #                                   Output
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Creating output requests ...',True)

    # field output
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Field output ...',True)

    for step in parameters['steps'].values():
        model.FieldOutputRequest(name='F-Output-1',createStepName=step['name'],variables=('U','RF','S','E','EE','COORD',))
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    # history output
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'History output ...',True)

    for step in parameters['steps'].values():
        model.HistoryOutputRequest(name='H-Output-1',createStepName=step['name'])
        if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
            model.historyOutputRequests['H-Output-1'].setValues(contourIntegral='DebondUp',sectionPoints=DEFAULT,rebar=EXCLUDE,numberOfContours=parameters['Jintegral']['numberOfContours'])
            model.historyOutputRequests['H-Output-2'].setValues(contourIntegral='DebondLow',sectionPoints=DEFAULT,rebar=EXCLUDE,numberOfContours=parameters['Jintegral']['numberOfContours'])
        else:
            model.historyOutputRequests['H-Output-1'].setValues(contourIntegral='Debond',sectionPoints=DEFAULT,rebar=EXCLUDE,numberOfContours=parameters['Jintegral']['numberOfContours'])

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #===============================================================================#
    #                                Job creation
    #===============================================================================#

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Creating and submitting job ...',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Set job name',True)
    modelData['jobname'] = 'Job-Jintegral-' + modelname

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create job with name ' + modelData['jobname'],True)
    mdb.Job(name=modelData['jobname'], model=modelname, description='', type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=99, memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=ON, modelPrint=ON, contactPrint=ON, historyPrint=ON, userSubroutine='',scratch='', multiprocessingMode=DEFAULT, numCpus=parameters['solver']['cpus'], numDomains=12,numGPUs=0)

    mdb.save()

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Submit job and wait for completion',True)
    localStart = timeit.default_timer()
    #mdb.jobs['Job-' + modelname].submit(consistencyChecking=OFF)
    mdb.jobs[modelData['jobname']].writeInput(consistencyChecking=OFF)
    mdb.jobs[modelData['jobname']].waitForCompletion()

    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Job time: ' + str(timeit.default_timer() - localStart) + ' [s]',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Closing database ...',True)
    mdb.save()
    mdb.close()

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Exiting function: createRVE(parameters,logfilepath,logindent)',True)

    return modelData

def modifyRVEinputfile(parameters,mdbData,logfilepath,baselogindent,logindent):
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: modifyRVE(parameters,mdbData)',True)
    skipLineToLogFile(logfilepath,'a',True)
    theta = parameters['geometry']['theta']
    # odb name and path
    #odbname = mdbData['jobname'] + '.odb'
    #odbfullpath = join(parameters['wd'],odbname)
    # input file name and path
    inpname = mdbData['jobname'] + '.inp'
    inpfullpath = join(parameters['input']['wd'],inpname)
    # modified input file name
    modinpname = 'Job-VCCTandJintegral-' + parameters['input']['modelname'] + '.inp'
    modinpfullpath = join(parameters['input']['wd'],modinpname)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Working directory: ' + parameters['input']['wd'],True)
    #writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'ODB database name: ' + odbname,True)
    #writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'ODB database full path: ' + join(parameters['wd'],odbname),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Input file name: ' + inpname,True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Input file full path: ' + join(parameters['input']['wd'],inpname),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Modified input file name: ' + modinpname,True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Modified input file full path: ' + join(parameters['input']['wd'],modinpname),True)
    createABQinpfile(modinpname)
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading content of original input file ...',True)
    with open(inpfullpath,'r') as inp:
        inpfilelines = inp.readlines()
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading nodes and saving to dictionary ...',True)
    nodes = {}
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            nodes[int(line.replace('\n','').split(',')[0])] = [float(line.replace('\n','').split(',')[1]),float(line.replace('\n','').split(',')[2])]
            store = False
            break
        elif store == True:
            nodes[int(line.replace('\n','').split(',')[0])] = [float(line.replace('\n','').split(',')[1]),float(line.replace('\n','').split(',')[2])]
        elif ('*Node' in line or '*NODE' in line) and len(inpfilelines[l+1].replace('\n','').split(','))==3:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading quadrilateral elements and saving to dictionary ...',True)
    quads = {}
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            quadIndex = int(line.replace('\n','').split(',')[0])
            quads[quadIndex] = []
            for node in line.replace('\n','').split(',')[1:]:
                quads[quadIndex].append(int(node))
            store = False
            break
        elif store == True:
            quadIndex = int(line.replace('\n','').split(',')[0])
            quads[quadIndex] = []
            for node in line.replace('\n','').split(',')[1:]:
                quads[quadIndex].append(int(node))
        elif ('*Element, type=CPE8' in line or '*ELEMENT, type=CPE8' in line or '*Element, type=CPE4' in line or '*ELEMENT, type=CPE4' in line) and (len(inpfilelines[l+1].replace('\n','').split(','))==5 or len(inpfilelines[l+1].replace('\n','').split(','))==9):
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading crack tip sets and saving to variable ...',True)
        for l,line in enumerate(inpfilelines):
            if ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['CRACKTIPUP','cracktipup']:
                cracktipupIndex = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                break
        for l,line in enumerate(inpfilelines):
            if ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['CRACKTIPLOW','cracktiplow']:
                cracktiplowIndex = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                break
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading crack tip set and saving to variable ...',True)
        for l,line in enumerate(inpfilelines):
            if ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['CRACKTIP','cracktip']:
                cracktipIndex = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                break
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading crack faces node set and saving to list ...',True)
    crackfacesNodeset = []
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    crackfacesNodeset.append(int(index))
            store = False
            break
        elif store == True:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    crackfacesNodeset.append(int(index))
        elif ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['CRACK','crack']:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading north side node set and saving to list ...',True)
    northSideNodeset = []
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    northSideNodeset.append(int(index))
            store = False
            break
        elif store == True:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    northSideNodeset.append(int(index))
        elif ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['UPPERSIDE','upperside']:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading right side node set and saving to list ...',True)
    rightSideNodeset = []
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    rightSideNodeset.append(int(index))
            store = False
            break
        elif store == True:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    rightSideNodeset.append(int(index))
        elif ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['RIGHTSIDE','rightside']:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading left side node set and saving to list ...',True)
    leftSideNodeset = []
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    leftSideNodeset.append(int(index))
            store = False
            break
        elif store == True:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    leftSideNodeset.append(int(index))
        elif ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['LEFTSIDE','leftside']:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading north-east corner node set and saving to variable ...',True)
    for l,line in enumerate(inpfilelines):
        if ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['NE-CORNER','ne-corner']:
            northeastIndex = int(inpfilelines[l+1].replace('\n','').split(',')[0])
            break
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading north-west corner node set  and saving to variable ...',True)
    for l,line in enumerate(inpfilelines):
        if ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['NW-CORNER','nw-corner']:
            northwestIndex = int(inpfilelines[l+1].replace('\n','').split(',')[0])
            break
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading south-east corner node set and saving to variable ...',True)
    for l,line in enumerate(inpfilelines):
        if ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['SE-CORNER','se-corner']:
            southeastIndex = int(inpfilelines[l+1].replace('\n','').split(',')[0])
            break
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading south-west corner node set  and saving to variable ...',True)
    for l,line in enumerate(inpfilelines):
        if ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['SW-CORNER','sw-corner']:
            southwestIndex = int(inpfilelines[l+1].replace('\n','').split(',')[0])
            break
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading crack faces element set and saving to list ...',True)
    crackfacesElementset = []
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    crackfacesElementset.append(int(index))
            store = False
            break
        elif store == True:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    crackfacesElementset.append(int(index))
        elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['CRACK','crack']:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading fiber node set and saving to list ...',True)
    fiberNodeset = []
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    fiberNodeset.append(int(index))
            store = False
            break
        elif store == True:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    fiberNodeset.append(int(index))
        elif ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER','fiber']:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading matrix node set and saving to list ...',True)
    matrixNodeset = []
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    matrixNodeset.append(int(index))
            store = False
            break
        elif store == True:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    matrixNodeset.append(int(index))
        elif ('*Nset' in line or '*NSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX','matrix']:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading fiber element set and saving to list ...',True)
    fiberElementset = []
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    fiberElementset.append(int(index))
            store = False
            break
        elif store == True:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    fiberElementset.append(int(index))
        elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER','fiber']:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading matrix element set and saving to list ...',True)
    matrixElementset = []
    store = False
    for l,line in enumerate(inpfilelines):
        if store == True and '*' in inpfilelines[l+1]:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    matrixElementset.append(int(index))
            store = False
            break
        elif store == True:
            for index in line.replace('\n','').split(','):
                if index!='' and index!=' ':
                    matrixElementset.append(int(index))
        elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX','matrix']:
            store = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set FIBER-EXTANNULUS-UPPERCRACK-CTUP and saving to list ...',True)
        fiberExtannUppcrackCtUpElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannUppcrackCtUpElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannUppcrackCtUpElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-UPPERCRACK-CTUP','fiber-extannulus-uppercrack-ctup'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    fiberExtannUppcrackCtUpElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-UPPERCRACK-CTUP','fiber-extannulus-uppercrack-ctup']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set FIBER-EXTANNULUS-UPPERCRACK-CTLOW and saving to list ...',True)
        fiberExtannUppcrackCtLowElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannUppcrackCtLowElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannUppcrackCtLowElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-UPPERCRACK-CTLOW','fiber-extannulus-uppercrack-ctlow'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    fiberExtannUppcrackCtLowElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-UPPERCRACK-CTLOW','fiber-extannulus-uppercrack-ctlow']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set FIBER-EXTANNULUS-UPPERCRACK and saving to list ...',True)
        fiberExtannUppcrackElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannUppcrackElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannUppcrackElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-UPPERCRACK','fiber-extannulus-uppercrack'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    fiberExtannUppcrackElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-UPPERCRACK','fiber-extannulus-uppercrack']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set FIBER-EXTANNULUS-FIRSTBOUNDED-CTUP and saving to list ...',True)
        fiberExtannFirstbounCtUpElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannFirstbounCtUpElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannFirstbounCtUpElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-FIRSTBOUNDED-CTUP','fiber-extannulus-firstbounded-ctup'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    fiberExtannFirstbounCtUpElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-FIRSTBOUNDED-CTUP','fiber-extannulus-firstbounded-ctup']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set FIBER-EXTANNULUS-FIRSTBOUNDED-CTLOW and saving to list ...',True)
        fiberExtannFirstbounCtLowElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannFirstbounCtLowElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannFirstbounCtLowElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-FIRSTBOUNDED-CTLOW','fiber-extannulus-firstbounded-ctlow'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    fiberExtannFirstbounCtLowElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-FIRSTBOUNDED-CTLOW','fiber-extannulus-firstbounded-ctlow']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set FIBER-EXTANNULUS-FIRSTBOUNDED and saving to list ...',True)
        fiberExtannFirstbounElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannFirstbounElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        fiberExtannFirstbounElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-FIRSTBOUNDED','fiber-extannulus-firstbounded'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    fiberExtannFirstbounElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['FIBER-EXTANNULUS-FIRSTBOUNDED','fiber-extannulus-firstbounded']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set MATRIX-INTANNULUS-UPPERCRACK-CTUP and saving to list ...',True)
        matrixIntannUppcrackCtUpElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannUppcrackCtUpElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannUppcrackCtUpElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-UPPERCRACK-CTUP','matrix-intannulus-uppercrack-ctup'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    matrixIntannUppcrackCtUpElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-UPPERCRACK-CTUP','matrix-intannulus-uppercrack-ctup']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set MATRIX-INTANNULUS-UPPERCRACK-CTLOW and saving to list ...',True)
        matrixIntannUppcrackCtLowElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannUppcrackCtLowElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannUppcrackCtLowElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-UPPERCRACK-CTLOW','matrix-intannulus-uppercrack-ctlow'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    matrixIntannUppcrackCtLowElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-UPPERCRACK-CTLOW','matrix-intannulus-uppercrack-ctlow']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set MATRIX-INTANNULUS-UPPERCRACK and saving to list ...',True)
        matrixIntannUppcrackElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannUppcrackElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannUppcrackElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-UPPERCRACK','matrix-intannulus-uppercrack'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    matrixIntannUppcrackElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-UPPERCRACK','matrix-intannulus-uppercrack']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set MATRIX-INTANNULUS-FIRSTBOUNDED-CTUP and saving to list ...',True)
        matrixIntannFirstbounCtUpElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannFirstbounCtUpElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannFirstbounCtUpElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-FIRSTBOUNDED-CTUP','matrix-intannulus-firstbounded-ctup'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    matrixIntannFirstbounCtUpElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-FIRSTBOUNDED-CTUP','matrix-intannulus-firstbounded-ctup']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set MATRIX-INTANNULUS-FIRSTBOUNDED-CTLOW and saving to list ...',True)
        matrixIntannFirstbounCtLowElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannFirstbounCtLowElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannFirstbounCtLowElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-FIRSTBOUNDED-CTLOW','matrix-intannulus-firstbounded-ctlow'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    matrixIntannFirstbounCtLowElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-FIRSTBOUNDED-CTLOW','matrix-intannulus-firstbounded-ctlow']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Reading element set MATRIX-INTANNULUS-FIRSTBOUNDED and saving to list ...',True)
        matrixIntannFirstbounElementset = []
        store = False
        for l,line in enumerate(inpfilelines):
            if store == True and '*' in inpfilelines[l+1]:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannFirstbounElementset.append(int(index))
                        store = False
                        break
            elif store == True:
                for index in line.replace('\n','').split(','):
                    if index!='' and index!=' ':
                        matrixIntannFirstbounElementset.append(int(index))
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-FIRSTBOUNDED','matrix-intannulus-firstbounded'] and line.replace('\n','').split(',')[2].replace(' ','') in ['GENERATE','generate']:
                store = False
                startEl = int(inpfilelines[l+1].replace('\n','').split(',')[0])
                endEl = int(inpfilelines[l+1].replace('\n','').split(',')[1])
                deltaEl = int(inpfilelines[l+1].replace('\n','').split(',')[2])
                for index in range(startEl,endEl+deltaEl,deltaEl):
                    matrixIntannFirstbounElementset.append(index)
                break
            elif ('*Elset' in line or '*ELSET' in line) and line.replace('\n','').split(',')[1].split('=')[1] in ['MATRIX-INTANNULUS-FIRSTBOUNDED','matrix-intannulus-firstbounded']:
                store = True
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create node set NORTH-SIDE-WITHOUT-CORNERS ...',True)
    northSideWithoutCornersNodeset = []
    for node in northSideNodeset:
        if not node in [northeastIndex,northwestIndex]:
            northSideWithoutCornersNodeset.append(node)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create node set NORTH-SIDE-CENTER ...',True)
    for node in northSideNodeset:
        if nodes[node][0]==0.0:
            northSideCenter = node
            break
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Node ' + str(northSideCenter) + ' is at the center of the NORTH boundary',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create node set NORTH-SIDE-POSSIDE ...',True)
    northSidePosSide = []
    for node in northSideNodeset:
        if nodes[node][0]>0.0:
            northSidePosSide.append(node)
    northSidePosSideCoords = [nodes[i][0] for i in northSidePosSide]
    northSidePosSide = np.array(northSidePosSide)[np.argsort(northSidePosSideCoords)].tolist()
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Set northSidePosSide contains ' + str(len(northSidePosSide)) + ' nodes',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create node set NORTH-SIDE-NEGSIDE ...',True)
    northSideNegSide = []
    for node in northSideNodeset:
        if nodes[node][0]<0.0:
            northSideNegSide.append(node)
    northSideNegSideCoords = [nodes[i][0] for i in northSideNegSide]
    northSideNegSide = np.array(northSideNegSide)[np.argsort(northSideNegSideCoords)].tolist()
    northSideNegSide = northSideNegSide[::-1]
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Set northSideNegSide contains ' + str(len(northSideNegSide)) + ' nodes',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create node set RIGHT-SIDE-WITHOUT-CORNERS ...',True)
    rightSideWithoutCornersNodeset = []
    for node in rightSideNodeset:
        if not node in [northeastIndex,southeastIndex]:
            rightSideWithoutCornersNodeset.append(node)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Create node set LEFT-SIDE-WITHOUT-CORNERS ...',True)
    leftSideWithoutCornersNodeset = []
    for node in leftSideNodeset:
        if not node in [southwestIndex,northwestIndex]:
            leftSideWithoutCornersNodeset.append(node)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Insert new coincident node(s) at the crack tip and create dummy node(s) ...',True)
    numNodes = mdbData['numNodes']
    numEls = mdbData['numEls']
    numQuads = mdbData['numQuads']
    numTris = mdbData['numTris']
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Total number of nodes = ' + str(numNodes),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Total number of elements = ' + str(numEls),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Total number of quadrilateral elements = ' + str(numQuads),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Total number of triangular elements = ' + str(numTris),True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Index of current crack tip nodes: ' + str(cracktipUPIndex) + ', ' + str(cracktipLOWIndex),True)
        matrixCracktipUPIndex = numNodes + 1000
        cracktipUPDummyIndex = numNodes + 1000 + 1
        matrixCracktipLOWIndex = numNodes + 1000 + 50
        cracktipLOWDummyIndex = numNodes + 1000 + 50 + 1
        nodes[matrixCracktipUPIndex] = [nodes[cracktipUPIndex][0],nodes[cracktipUPIndex][1]]
        nodes[cracktipUPDummyIndex] = [-5*parameters['geometry']['Rf'],-10*parameters['geometry']['Rf']]
        nodes[matrixCracktipLOWIndex] = [nodes[cracktipLOWIndex][0],nodes[cracktipLOWIndex][1]]
        nodes[cracktipLOWDummyIndex] = [-5*parameters['geometry']['Rf'],-20*parameters['geometry']['Rf']]
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix upper crack tip node with index ' + str(matrixCracktipUPIndex) + ' and coordinates (' + str(nodes[cracktipUPIndex][0]) + ', '+ str(nodes[cracktipUPIndex][1]) + ')',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix upper crack tip dummy node with index ' + str(cracktipUPDummyIndex)+ ' and coordinates (' + str(-5*parameters['geometry']['Rf']) + ', '+ str(-10*parameters['geometry']['Rf']) + ')',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix lower crack tip node with index ' + str(matrixCracktipLOWIndex) + ' and coordinates (' + str(nodes[cracktipLOWIndex][0]) + ', '+ str(nodes[cracktipLOWIndex][1]) + ')',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix lower crack tip dummy node with index ' + str(cracktipLOWDummyIndex)+ ' and coordinates (' + str(-5*parameters['geometry']['Rf']) + ', '+ str(-20*parameters['geometry']['Rf']) + ')',True)
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Index of current crack tip node: ' + str(cracktipIndex),True)
        matrixCracktipIndex = numNodes + 1000
        cracktipDummyIndex = numNodes + 1000 + 1
        nodes[matrixCracktipIndex] = [nodes[cracktipIndex][0],nodes[cracktipIndex][1]]
        nodes[cracktipDummyIndex] = [-5*parameters['geometry']['Rf'],-10*parameters['geometry']['Rf']]
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix crack tip node with index ' + str(matrixCracktipIndex) + ' and coordinates (' + str(nodes[cracktipIndex][0]) + ', '+ str(nodes[cracktipIndex][1]) + ')',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix dummy node with index ' + str(cracktipDummyIndex)+ ' and coordinates (' + str(-5*parameters['geometry']['Rf']) + ', '+ str(-10*parameters['geometry']['Rf']) + ')',True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Searching for elements connected to the upper crack tip',True)
        fiberElswithCracktipUP = []
        matrixElswithCracktipUP = []
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Found',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  On fiber',True)
        for element in fiberExtannUppcrackCtUpElementset:
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    fiberElswithCracktipUP.append(element)
                    firstdebondedFiberElUP = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Debonded element: ' + str(element),True)
                    break
        for e in range(len(fiberExtannFirstbounCtUpElementset)-1,-1,-1):
            element = fiberExtannFirstbounElementset[e]
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    fiberElswithCracktipUP.append(element)
                    firstboundedFiberElUP = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Bonded element: ' + str(element),True)
                    break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  On matrix',True)
        for element in matrixIntannUppcrackCtUpElementset:
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    matrixElswithCracktipUP.append(element)
                    firstdebondedMatrixElUP = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Debonded element: ' + str(element),True)
                    break
        for element in matrixIntannFirstbounCtUpElementset:
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    matrixElswithCracktipUP.append(element)
                    firstboundedMatrixElUP = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Bonded element: ' + str(element),True)
                    break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Searching for elements connected to the lower crack tip',True)
        fiberElswithCracktipLOW = []
        matrixElswithCracktipLOW = []
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Found',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  On fiber',True)
        for element in fiberExtannUppcrackCtLowElementset:
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    fiberElswithCracktipLOW.append(element)
                    firstdebondedFiberElLOW = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Debonded element: ' + str(element),True)
                    break
        for e in range(len(fiberExtannFirstbounCtLowElementset)-1,-1,-1):
            element = fiberExtannFirstbounElementset[e]
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    fiberElswithCracktipLOW.append(element)
                    firstboundedFiberElLOW = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Bonded element: ' + str(element),True)
                    break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  On matrix',True)
        for element in matrixIntannUppcrackCtLowElementset:
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    matrixElswithCracktipLOW.append(element)
                    firstdebondedMatrixElLOW = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Debonded element: ' + str(element),True)
                    break
        for element in matrixIntannFirstbounCtLowElementset:
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    matrixElswithCracktipLOW.append(element)
                    firstboundedMatrixElLOW = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Bonded element: ' + str(element),True)
                    break
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Searching for elements connected to the crack tip',True)
        fiberElswithCracktip = []
        matrixElswithCracktip = []
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Found',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  On fiber',True)
        for element in fiberExtannUppcrackElementset:
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    fiberElswithCracktip.append(element)
                    firstdebondedFiberEl = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Debonded element: ' + str(element),True)
                    break
        for e in range(len(fiberExtannFirstbounElementset)-1,-1,-1):
            element = fiberExtannFirstbounElementset[e]
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    fiberElswithCracktip.append(element)
                    firstboundedFiberEl = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Bonded element: ' + str(element),True)
                    break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '  On matrix',True)
        for element in matrixIntannUppcrackElementset:
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    matrixElswithCracktip.append(element)
                    firstdebondedMatrixEl = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Debonded element: ' + str(element),True)
                    break
        for element in matrixIntannFirstbounElementset:
            if element in quads.keys():
                if cracktipIndex in quads[element]:
                    matrixElswithCracktip.append(element)
                    firstboundedMatrixEl = element
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - Bonded element: ' + str(element),True)
                    break
    if 'second' in parameters['mesh']['elements']['order']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Second order elements are used',True)
        if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
            matrixFirstBehindCracktipUPIndex = numNodes + 1000 + 2
            firstBehindCracktipUPDummyIndex = numNodes + 1000 + 3
            matrixFirstBehindCracktipLOWUPIndex = numNodes + 1000 + 50 + 2
            firstBehindCracktipLOWDummyIndex = numNodes + 1000 + 50 + 3
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix first behind upper crack tip node with index ' + str(matrixFirstBehindCracktipUPIndex),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating upper crack tip dummy node with index ' + str(firstBehindCracktipUPDummyIndex),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix first behind lower crack tip node with index ' + str(matrixFirstBehindCracktipLOWIndex),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating lower crack tip dummy node with index ' + str(firstBehindCracktipLOWDummyIndex),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Find common nodes of bounded upper crack tip elements on fiber and matrix',True)
            commonNodesUP = []
            fiberElnodesUP = quads[firstboundedFiberElUP]
            matrixElnodesUP = quads[firstboundedMatrixElUP]
            for node in fiberElnodesUP:
                if node in matrixElnodesUP:
                    commonNodesUP.append(node)
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - node ' + str(node),True)
                    if len(commonNodesUP)==3:
                        break
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute distances of bounded nodes from upper cracktip',True)
            distancesUP = []
            for node in commonNodesUP:
                if node != cracktipUPIndex:
                    distancesUP.append(np.sqrt((nodes[node][0]-nodes[cracktipUPIndex][0])*(nodes[node][0]-nodes[cracktipUPIndex][0])+(nodes[node][1]-nodes[cracktipUPIndex][1])*(nodes[node][1]-nodes[cracktipUPIndex][1])))
                else:
                    distancesUP.append(0.0)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Reordering labels based on distances',True)
            fiberFirstBehindCracktipUPIndex = commonNodesUP[np.argsort(distancesUP)[-2]] # argsort goes from smaller to higher
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                fiberSecondBehindCracktipUPIndex = commonNodesUP[np.argsort(distancesUP)[-1]]
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix upper crack tip node with index ' + str(matrixFirstBehindCracktipUPIndex) + ' and coordinates (' + str(nodes[fiberFirstBehindCracktipUPIndex][0]) + ', '+ str(nodes[fiberFirstBehindCracktipUPIndex][1]) + ')',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating upper crack tip dummy node with index ' + str(firstBehindCracktipUPDummyIndex)+ ' and coordinates (' + str(5*parameters['geometry']['Rf']) + ', '+ str(-10*parameters['geometry']['Rf']) + ')',True)
            nodes[matrixFirstBehindCracktipUPIndex] = [nodes[fiberFirstBehindCracktipUPIndex][0],nodes[fiberFirstBehindCracktipUPIndex][1]]
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                nodes[matrixSecondBehindCracktipUPIndex] = [nodes[fiberSecondBehindCracktipUPIndex][0],nodes[fiberSecondBehindCracktipUPIndex][1]]
            nodes[firstBehindCracktipUPDummyIndex] = [5*parameters['geometry']['Rf'],-10*parameters['geometry']['Rf']]
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                nodes[secondBehindCracktipUPDummyIndex] = [5*parameters['geometry']['Rf'],-20*parameters['geometry']['Rf']]
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Find common nodes of bounded lower crack tip elements on fiber and matrix',True)
            commonNodesLOW = []
            fiberElnodesLOW = quads[firstboundedFiberElLOW]
            matrixElnodesLOW = quads[firstboundedMatrixElLOW]
            for node in fiberElnodesLOW:
                if node in matrixElnodesLOW:
                    commonNodesLOW.append(node)
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - node ' + str(node),True)
                    if len(commonNodesLOW)==3:
                        break
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute distances of bounded nodes from lower cracktip',True)
            distancesLOW = []
            for node in commonNodesLOW:
                if node != cracktipLOWIndex:
                    distancesLOW.append(np.sqrt((nodes[node][0]-nodes[cracktipLOWIndex][0])*(nodes[node][0]-nodes[cracktipLOWIndex][0])+(nodes[node][1]-nodes[cracktipLOWIndex][1])*(nodes[node][1]-nodes[cracktipLOWIndex][1])))
                else:
                    distancesLOW.append(0.0)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Reordering labels based on distances',True)
            fiberFirstBehindCracktipLOWIndex = commonNodesLOW[np.argsort(distancesLOW)[-2]] # argsort goes from smaller to higher
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                fiberSecondBehindCracktipLOWIndex = commonNodesLOW[np.argsort(distancesLOW)[-1]]
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix lower crack tip node with index ' + str(matrixFirstBehindCracktipLOWIndex) + ' and coordinates (' + str(nodes[fiberFirstBehindCracktipLOWIndex][0]) + ', '+ str(nodes[fiberFirstBehindCracktipLOWIndex][1]) + ')',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating lower crack tip dummy node with index ' + str(firstBehindCracktipLOWDummyIndex)+ ' and coordinates (' + str(5*parameters['geometry']['Rf']) + ', '+ str(-20*parameters['geometry']['Rf']) + ')',True)
            nodes[matrixFirstBehindCracktipLOWIndex] = [nodes[fiberFirstBehindCracktipLOWIndex][0],nodes[fiberFirstBehindCracktipLOWIndex][1]]
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                nodes[matrixSecondBehindCracktipLOWIndex] = [nodes[fiberSecondBehindCracktipLOWIndex][0],nodes[fiberSecondBehindCracktipLOWIndex][1]]
            nodes[firstBehindCracktipLOWDummyIndex] = [5*parameters['geometry']['Rf'],-20*parameters['geometry']['Rf']]
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                nodes[secondBehindCracktipLOWDummyIndex] = [5*parameters['geometry']['Rf'],-40*parameters['geometry']['Rf']]
        else:
            matrixFirstBehindCracktipIndex = numNodes + 1000 + 2
            firstBehindCracktipDummyIndex = numNodes + 1000 + 3
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix first behind crack tip node with index ' + str(matrixFirstBehindCracktipIndex),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix dummy node with index ' + str(firstBehindCracktipDummyIndex),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Find common nodes of bounded crack tip elements on fiber and matrix',True)
            commonNodes = []
            fiberElnodes = quads[firstboundedFiberEl]
            matrixElnodes = quads[firstboundedMatrixEl]
            for node in fiberElnodes:
                if node in matrixElnodes:
                    commonNodes.append(node)
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '   - node ' + str(node),True)
                    if len(commonNodes)==3:
                        break
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute distances of bounded nodes from cracktip',True)
            distances = []
            for node in commonNodes:
                if node != cracktipIndex:
                    distances.append(np.sqrt((nodes[node][0]-nodes[cracktipIndex][0])*(nodes[node][0]-nodes[cracktipIndex][0])+(nodes[node][1]-nodes[cracktipIndex][1])*(nodes[node][1]-nodes[cracktipIndex][1])))
                else:
                    distances.append(0.0)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Reordering labels based on distances',True)
            fiberFirstBehindCracktipIndex = commonNodes[np.argsort(distances)[-2]] # argsort goes from smaller to higher
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                fiberSecondBehindCracktipIndex = commonNodes[np.argsort(distances)[-1]]
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix crack tip node with index ' + str(matrixFirstBehindCracktipIndex) + ' and coordinates (' + str(nodes[fiberFirstBehindCracktipIndex][0]) + ', '+ str(nodes[fiberFirstBehindCracktipIndex][1]) + ')',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Creating matrix dummy node with index ' + str(firstBehindCracktipDummyIndex)+ ' and coordinates (' + str(5*parameters['geometry']['Rf']) + ', '+ str(-10*parameters['geometry']['Rf']) + ')',True)
            nodes[matrixFirstBehindCracktipIndex] = [nodes[fiberFirstBehindCracktipIndex][0],nodes[fiberFirstBehindCracktipIndex][1]]
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                nodes[matrixSecondBehindCracktipIndex] = [nodes[fiberSecondBehindCracktipIndex][0],nodes[fiberSecondBehindCracktipIndex][1]]
            nodes[firstBehindCracktipDummyIndex] = [5*parameters['geometry']['Rf'],-10*parameters['geometry']['Rf']]
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                nodes[secondBehindCracktipDummyIndex] = [5*parameters['geometry']['Rf'],-40*parameters['geometry']['Rf']]
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Identify nodes on crack faces for displacement measurements ...',True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Find nodes belonging to the fiber elements around the upper crack tip',True)
        nodesAroundCracktipUP = quads[firstdebondedFiberElUP]
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Of these, identify the ones beloging to the crack surface',True)
        nodesFiberDisplacementMeasUP = []
        for node in nodesAroundCracktipUP:
            if node in crackfacesNodeset and node!=cracktipUPIndex:
                nodesFiberDisplacementMeasUP.append(node)
                if len(nodesFiberDisplacementMeasUP)==2:
                    break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Found ' + str(len(nodesFiberDisplacementMeasUP)) + ' nodes',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute distances of debonded nodes from cracktip',True)
        distancesFiberDisplacementMeasUP = []
        for node in nodesFiberDisplacementMeasUP:
            distancesFiberDisplacementMeasUP.append(np.sqrt((nodes[node][0]-nodes[cracktipUPIndex][0])*(nodes[node][0]-nodes[cracktipUPIndex][0])+(nodes[node][1]-nodes[cracktipUPIndex][1])*(nodes[node][1]-nodes[cracktipUPIndex][1])))
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Find nodes belonging to the matrix elements around the upper crack tip',True)
        nodesAroundCracktipUP = quads[firstdebondedMatrixElUP]
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Of these, identify the ones beloging to the crack surface',True)
        nodesMatrixDisplacementMeasUP = []
        for node in nodesAroundCracktipUP:
            if node in crackfacesNodeset and node!=cracktipUPIndex:
                nodesMatrixDisplacementMeasUP.append(node)
            if len(nodesMatrixDisplacementMeasUP)==2:
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Found ' + str(len(nodesMatrixDisplacementMeasUP)) + ' nodes',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute distances of debonded nodes from upper cracktip',True)
        distancesMatrixDisplacementMeasUP = []
        for node in nodesMatrixDisplacementMeasUP:
            distancesMatrixDisplacementMeasUP.append(np.sqrt((nodes[node][0]-nodes[cracktipUPIndex][0])*(nodes[node][0]-nodes[cracktipUPIndex][0])+(nodes[node][1]-nodes[cracktipUPIndex][1])*(nodes[node][1]-nodes[cracktipUPIndex][1])))
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Sort lists with computed distances',True)
        sortedFiberDistanceIndecesUP = np.argsort(distancesFiberDisplacementMeasUP)
        sortedMatrixDistanceIndecesUP = np.argsort(distancesMatrixDisplacementMeasUP)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Indeces to sort fiber nodes ' + str(sortedFiberDistanceIndecesUP),True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Indeces to sort matrix nodes ' + str(sortedMatrixDistanceIndecesUP),True)
        if 'second' in parameters['mesh']['elements']['order']:
            cracktipFiberDispMeasIndexUP = nodesFiberDisplacementMeasUP[sortedFiberDistanceIndecesUP[-1]]
            firstBehindCracktipFiberDispMeasIndexUP = nodesFiberDisplacementMeasUP[sortedFiberDistanceIndecesUP[-2]]
            cracktipMatrixDispMeasIndexUP = nodesMatrixDisplacementMeasUP[sortedMatrixDistanceIndecesUP[-1]]
            firstBehindCracktipMatrixDispMeasIndexUP = nodesMatrixDisplacementMeasUP[sortedMatrixDistanceIndecesUP[-2]]
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the matrix crack tip is measured on node ' + str(cracktipMatrixDispMeasIndexUP),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the first bonded node behind the matrix crack tip is measured on node ' + str(firstBehindCracktipMatrixDispMeasIndexUP),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the fiber crack tip is measured on node ' + str(cracktipFiberDispMeasIndexUP),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the first bonded node behind the fiber crack tip is measured on node ' + str(firstBehindCracktipFiberDispMeasIndexUP),True)
        else:
            cracktipFiberDispMeasIndexUP = nodesFiberDisplacementMeasUP[sortedFiberDistanceIndecesUP[-1]]
            cracktipMatrixDispMeasIndexUP = nodesMatrixDisplacementMeasUP[sortedMatrixDistanceIndecesUP[-1]]
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Find nodes belonging to the fiber elements around the lower crack tip',True)
        nodesAroundCracktipLOW = quads[firstdebondedFiberElLOW]
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Of these, identify the ones beloging to the crack surface',True)
        nodesFiberDisplacementMeasLOW = []
        for node in nodesAroundCracktipLOW:
            if node in crackfacesNodeset and node!=cracktipLOWIndex:
                nodesFiberDisplacementMeasLOW.append(node)
            if len(nodesFiberDisplacementMeasLOW)==2:
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Found ' + str(len(nodesFiberDisplacementMeasLOW)) + ' nodes',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute distances of debonded nodes from cracktip',True)
        distancesFiberDisplacementMeasLOW = []
        for node in nodesFiberDisplacementMeasLOW:
            distancesFiberDisplacementMeasLOW.append(np.sqrt((nodes[node][0]-nodes[cracktipLOWIndex][0])*(nodes[node][0]-nodes[cracktipLOWIndex][0])+(nodes[node][1]-nodes[cracktipLOWIndex][1])*(nodes[node][1]-nodes[cracktipLOWIndex][1])))
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Find nodes belonging to the matrix elements around the lower crack tip',True)
        nodesAroundCracktipLOW = quads[firstdebondedMatrixElLOW]
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Of these, identify the ones beloging to the crack surface',True)
        nodesMatrixDisplacementMeasLOW = []
        for node in nodesAroundCracktipLOW:
            if node in crackfacesNodeset and node!=cracktipLOWIndex:
                nodesMatrixDisplacementMeasLOW.append(node)
            if len(nodesMatrixDisplacementMeasLOW)==2:
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Found ' + str(len(nodesMatrixDisplacementMeasLOW)) + ' nodes',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute distances of debonded nodes from lower cracktip',True)
        distancesMatrixDisplacementMeasLOW = []
        for node in nodesMatrixDisplacementMeasLOW:
            distancesMatrixDisplacementMeasLOW.append(np.sqrt((nodes[node][0]-nodes[cracktipLOWIndex][0])*(nodes[node][0]-nodes[cracktipLOWIndex][0])+(nodes[node][1]-nodes[cracktipLOWIndex][1])*(nodes[node][1]-nodes[cracktipLOWIndex][1])))
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Sort lists with computed distances',True)
        sortedFiberDistanceIndecesLOW = np.argsort(distancesFiberDisplacementMeasLOW)
        sortedMatrixDistanceIndecesLOW = np.argsort(distancesMatrixDisplacementMeasLOW)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Indeces to sort fiber nodes ' + str(sortedFiberDistanceIndecesLOW),True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Indeces to sort matrix nodes ' + str(sortedMatrixDistanceIndecesLOW),True)
        if 'second' in parameters['mesh']['elements']['order']:
            cracktipFiberDispMeasIndexLOW = nodesFiberDisplacementMeasLOW[sortedFiberDistanceIndecesLOW[-1]]
            firstBehindCracktipFiberDispMeasIndexLOW = nodesFiberDisplacementMeasLOW[sortedFiberDistanceIndecesLOW[-2]]
            cracktipMatrixDispMeasIndexLOW = nodesMatrixDisplacementMeasLOW[sortedMatrixDistanceIndecesLOW[-1]]
            firstBehindCracktipMatrixDispMeasIndexLOW = nodesMatrixDisplacementMeasLOW[sortedMatrixDistanceIndecesLOW[-2]]
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the matrix crack tip is measured on node ' + str(cracktipMatrixDispMeasIndexLOW),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the first bonded node behind the matrix crack tip is measured on node ' + str(firstBehindCracktipMatrixDispMeasIndexLOW),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the fiber crack tip is measured on node ' + str(cracktipFiberDispMeasIndexLOW),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the first bonded node behind the fiber crack tip is measured on node ' + str(firstBehindCracktipFiberDispMeasIndexLOW),True)
        else:
            cracktipFiberDispMeasIndexLOW = nodesFiberDisplacementMeasLOW[sortedFiberDistanceIndecesLOW[-1]]
            cracktipMatrixDispMeasIndexLOW = nodesMatrixDisplacementMeasLOW[sortedMatrixDistanceIndecesLOW[-1]]
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Find nodes belonging to the fiber elements around the crack tip',True)
        nodesAroundCracktip = quads[firstdebondedFiberEl]
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Of these, identify the ones beloging to the crack surface',True)
        nodesFiberDisplacementMeas = []
        for node in nodesAroundCracktip:
            if node in crackfacesNodeset and node!=cracktipIndex:
                nodesFiberDisplacementMeas.append(node)
            if len(nodesFiberDisplacementMeas)==2:
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Found ' + str(len(nodesFiberDisplacementMeas)) + ' nodes',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute distances of debonded nodes from cracktip',True)
        distancesFiberDisplacementMeas = []
        for node in nodesFiberDisplacementMeas:
            distancesFiberDisplacementMeas.append(np.sqrt((nodes[node][0]-nodes[cracktipIndex][0])*(nodes[node][0]-nodes[cracktipIndex][0])+(nodes[node][1]-nodes[cracktipIndex][1])*(nodes[node][1]-nodes[cracktipIndex][1])))
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Find nodes belonging to the matrix elements around the crack tip',True)
        nodesAroundCracktip = quads[firstdebondedMatrixEl]
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Of these, identify the ones beloging to the crack surface',True)
        nodesMatrixDisplacementMeas = []
        for node in nodesAroundCracktip:
            if node in crackfacesNodeset and node!=cracktipIndex:
                nodesMatrixDisplacementMeas.append(node)
            if len(nodesMatrixDisplacementMeas)==2:
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Found ' + str(len(nodesMatrixDisplacementMeas)) + ' nodes',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute distances of debonded nodes from cracktip',True)
        distancesMatrixDisplacementMeas = []
        for node in nodesMatrixDisplacementMeas:
            distancesMatrixDisplacementMeas.append(np.sqrt((nodes[node][0]-nodes[cracktipIndex][0])*(nodes[node][0]-nodes[cracktipIndex][0])+(nodes[node][1]-nodes[cracktipIndex][1])*(nodes[node][1]-nodes[cracktipIndex][1])))
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Sort lists with computed distances',True)
        sortedFiberDistanceIndeces = np.argsort(distancesFiberDisplacementMeas)
        sortedMatrixDistanceIndeces = np.argsort(distancesMatrixDisplacementMeas)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Indeces to sort fiber nodes ' + str(sortedFiberDistanceIndeces),True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Indeces to sort matrix nodes ' + str(sortedMatrixDistanceIndeces),True)
        if 'second' in parameters['mesh']['elements']['order']:
            cracktipFiberDispMeasIndex = nodesFiberDisplacementMeas[sortedFiberDistanceIndeces[-1]]
            firstBehindCracktipFiberDispMeasIndex = nodesFiberDisplacementMeas[sortedFiberDistanceIndeces[-2]]
            cracktipMatrixDispMeasIndex = nodesMatrixDisplacementMeas[sortedMatrixDistanceIndeces[-1]]
            firstBehindCracktipMatrixDispMeasIndex = nodesMatrixDisplacementMeas[sortedMatrixDistanceIndeces[-2]]
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the matrix crack tip is measured on node ' + str(cracktipMatrixDispMeasIndex),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the first bonded node behind the matrix crack tip is measured on node ' + str(firstBehindCracktipMatrixDispMeasIndex),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the fiber crack tip is measured on node ' + str(cracktipFiberDispMeasIndex),True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Displacement for the first bonded node behind the fiber crack tip is measured on node ' + str(firstBehindCracktipFiberDispMeasIndex),True)
        else:
            cracktipFiberDispMeasIndex = nodesFiberDisplacementMeas[sortedFiberDistanceIndeces[-1]]
            cracktipMatrixDispMeasIndex = nodesMatrixDisplacementMeas[sortedMatrixDistanceIndeces[-1]]
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Assign new crack tip nodes to matrix elements at upper crack tip ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Assign new crack tip index to the bonded element on the matrix',True)
        for n,node in enumerate(quads[firstboundedMatrixElUP]):
            if node == cracktipUPIndex:
                quads[firstboundedMatrixElUP][n] = matrixCracktipUPIndex
        if 'second' in parameters['mesh']['elements']['order']:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Assign new first behind upper crack tip index to the bonded element on the matrix',True)
            for n,node in enumerate(quads[firstboundedMatrixElUP]):
                if node == fiberFirstBehindCracktipUPIndex:
                    quads[firstboundedMatrixElUP][n] = matrixFirstBehindCracktipUPIndex
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                for n,node in enumerate(quads[firstboundedMatrixElUP]):
                    if node == fiberSecondBehindCracktipUPIndex:
                        quads[firstboundedMatrixElUP][n] = matrixSecondBehindCracktipUPIndex
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Assign new upper crack tip index to the debonded element on the matrix',True)
        for n,node in enumerate(quads[firstdebondedMatrixElUP]):
            if node == cracktipUPIndex:
                quads[firstdebondedMatrixElUP][n] = matrixCracktipUPIndex
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Assign new crack tip nodes to matrix elements at lower crack tip ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Assign new crack tip index to the bonded element on the matrix',True)
        for n,node in enumerate(quads[firstboundedMatrixElLOW]):
            if node == cracktipLOWIndex:
                quads[firstboundedMatrixElLOW][n] = matrixCracktipLOWIndex
        if 'second' in parameters['mesh']['elements']['order']:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Assign new first behind lower crack tip index to the bonded element on the matrix',True)
            for n,node in enumerate(quads[firstboundedMatrixElLOW]):
                if node == fiberFirstBehindCracktipLOWIndex:
                    quads[firstboundedMatrixElLOW][n] = matrixFirstBehindCracktipLOWIndex
                if 'inverseSquareRoot' in parameters['singularity']['type']:
                    for n,node in enumerate(quads[firstboundedMatrixElLOW]):
                        if node == fiberSecondBehindCracktipLOWIndex:
                            quads[firstboundedMatrixElLOW][n] = matrixSecondBehindCracktipLOWIndex
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Assign new lower crack tip index to the debonded element on the matrix',True)
        for n,node in enumerate(quads[firstdebondedMatrixElLOW]):
            if node == cracktipLOWIndex:
                quads[firstdebondedMatrixElLOW][n] = matrixCracktipLOWIndex
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Assign new crack tip nodes to matrix elements at crack tip ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Assign new crack tip index to the bonded element on the matrix',True)
        for n,node in enumerate(quads[firstboundedMatrixEl]):
            if node == cracktipIndex:
                quads[firstboundedMatrixEl][n] = matrixCracktipIndex
        if 'second' in parameters['mesh']['elements']['order']:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Assign new first behind crack tip index to the bonded element on the matrix',True)
            for n,node in enumerate(quads[firstboundedMatrixEl]):
                if node == fiberFirstBehindCracktipIndex:
                    quads[firstboundedMatrixEl][n] = matrixFirstBehindCracktipIndex
            if 'inverseSquareRoot' in parameters['singularity']['type']:
                for n,node in enumerate(quads[firstboundedMatrixEl]):
                    if node == fiberSecondBehindCracktipIndex:
                        quads[firstboundedMatrixEl][n] = matrixSecondBehindCracktipIndex
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Assign new crack tip index to the debonded element on the matrix',True)
        for n,node in enumerate(quads[firstdebondedMatrixEl]):
            if node == cracktipIndex:
                quads[firstdebondedMatrixEl][n] = matrixCracktipIndex
        writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Find set of debonded elements on fiber and on matrix  ...',True)
    crackfaceFiberElementset = []
    crackfaceMatrixElementset = []
    for element in crackfacesElementset:
        if element in fiberElementset:
            crackfaceFiberElementset.append(element)
        else:
            crackfaceMatrixElementset.append(element)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Find set of debonded nodes on fiber and on matrix  ...',True)
    crackfaceFiberNodeset = []
    crackfaceMatrixNodeset = []
    for node in crackfacesNodeset:
        if node in fiberNodeset:
            crackfaceFiberNodeset.append(node)
        else:
            crackfaceMatrixNodeset.append(node)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Writing new input file  ...',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Identify node section  ...',True)
    started = False
    for l,line in enumerate(inpfilelines):
        if started and '*' in line:
            nodeSecStop = l-1
            break
        elif ('*Node' in line or '*NODE' in line) and len(inpfilelines[l+1].replace('\n','').split(',')) == 3:
            nodeSecStart = l
            started = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Node section begins at line ' + str(nodeSecStart) + ' and ends at line ' + str(nodeSecStop),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Identify quadrilateral element section  ...',True)
    started = False
    for l,line in enumerate(inpfilelines):
        if started and '*' in line:
            elementSecStop = l-1
            break
        elif ('*Element, type=CPE8' in line or '*ELEMENT, type=CPE8' in line or '*Element, type=CPE4' in line or '*ELEMENT, type=CPE4' in line) and (len(inpfilelines[l+1].replace('\n','').split(','))==5 or len(inpfilelines[l+1].replace('\n','').split(','))==9):
            elementSecStart = l
            started = True
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Element section begins at line ' + str(elementSecStart) + ' and ends at line ' + str(elementSecStop),True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Identify end of assembly section  ...',True)
    for l,line in enumerate(inpfilelines):
        if '*End Assembly' in line or '*END ASSEMBLY' in line:
            endAssembly = l
            break
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    if len(parameters['steps'])>1:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Identify start of thermal step section  ...',True)
        for l,line in enumerate(inpfilelines):
            if '*Step, name=Temp-Step' in line or '*STEP, NAME=TEMP-STEP' in line:
                startTempStep = l
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Identify start of mechanical step section  ...',True)
        for l,line in enumerate(inpfilelines):
            if '*Step, name=Load-Step' in line or '*STEP, NAME=LOAD-STEP' in line:
                startLoadStep = l
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Identify start of thermal contour integral section  ...',True)
        for l,line in enumerate(inpfilelines):
            if ('*CONTOUR INTEGRAL' in line or '*Contour Integral' in line) and l>startTempStep and l<startLoadStep:
                startTempCI = l
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Identify start of mechanical contour integral section  ...',True)
        for l,line in enumerate(inpfilelines):
            if ('*CONTOUR INTEGRAL' in line or '*Contour Integral' in line) and l>startLoadStep:
                startLoadCI = l
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Identify start of boundary conditions section  ...',True)
        for l,line in enumerate(inpfilelines):
            if '** BOUNDARY CONDITIONS' in line or '** Boundary Conditions' in line:
                startBC = l
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Identify start of contour integral section  ...',True)
        for l,line in enumerate(inpfilelines):
            if '*CONTOUR INTEGRAL' in line or '*Contour Integral' in line:
                startCI = l
                endCI = l+1
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
    with open(modinpfullpath,'a') as inp:
        for line in inpfilelines[:nodeSecStart]:
            inp.write(line)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write nodes ...',True)
    with open(modinpfullpath,'a') as inp:
        inp.write('*NODE' + '\n')
        for node in nodes.keys():
            line = str(node)
            for coord in nodes[node]:
                line += ', ' + str(coord)
            inp.write(line + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
    with open(modinpfullpath,'a') as inp:
        for line in inpfilelines[nodeSecStop+1:elementSecStart]:
            inp.write(line)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write quadrilateral elements ...',True)
    with open(modinpfullpath,'a') as inp:
        inp.write(inpfilelines[elementSecStart])
        for quad in quads.keys():
            line = str(quad)
            for node in quads[quad]:
                line += ', ' + str(node)
            inp.write(line + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
    with open(modinpfullpath,'a') as inp:
        for line in inpfilelines[elementSecStop+1:endAssembly]:
            inp.write(line)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write crack faces node and element sets ...',True)
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=FIBER-CRACKFACE-NODES, INSTANCE=RVE-assembly' + '\n')
        line = ''
        for n,node in enumerate(crackfaceFiberNodeset):
            if n>0 and n%8==0.0:
                line += ' ' + str(node)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(node) + ','
        if len(line)>0:
            inp.write(line + '\n')
        inp.write('*NSET, NSET=MATRIX-CRACKFACE-NODES, INSTANCE=RVE-assembly' + '\n')
        line = ''
        for n,node in enumerate(crackfaceMatrixNodeset):
            if n>0 and n%8==0.0:
                line += ' ' + str(node)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(node) + ','
        if len(line)>0:
            inp.write(line + '\n')
        inp.write('*ELSET, ELSET=FIBER-CRACKFACE-ELEMENTS, INSTANCE=RVE-assembly' + '\n')
        line = ''
        for n,element in enumerate(crackfaceFiberElementset):
            if n>0 and n%8==0.0:
                line += ' ' + str(element)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(element) + ','
        if len(line)>0:
            inp.write(line + '\n')
        inp.write('*ELSET, ELSET=MATRIX-CRACKFACE-ELEMENTS, INSTANCE=RVE-assembly' + '\n')
        line = ''
        for n,element in enumerate(crackfaceMatrixElementset):
            if n>0 and n%8==0.0:
                line += ' ' + str(element)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(element) + ','
        if len(line)>0:
            inp.write(line + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write VCCT and J-integral node sets ...',True)
    if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
        with open(modinpfullpath,'a') as inp:
            inp.write('*NSET, NSET=FIBER-CRACKTIPUP, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipUPIndex) + '\n')
            inp.write('*NSET, NSET=MATRIX-CRACKTIPUP, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(matrixCracktipUPIndex) + '\n')
            inp.write('*NSET, NSET=CRACKTIPUP-CONTOURINTEGRAL, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipUPIndex) + ', ' + str(matrixCracktipUPIndex) + '\n')
            inp.write('*NSET, NSET=FIBER-CRACKTIPUP-DISPMEAS, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipFiberDispMeasIndexUP) + '\n')
            inp.write('*NSET, NSET=MATRIX-CRACKTIPUP-DISPMEAS, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipMatrixDispMeasIndexUP) + '\n')
            inp.write('*NSET, NSET=FIBER-CRACKTIPLOW, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipLOWIndex) + '\n')
            inp.write('*NSET, NSET=MATRIX-CRACKTIPLOW, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(matrixCracktipLOWIndex) + '\n')
            inp.write('*NSET, NSET=CRACKTIPLOW-CONTOURINTEGRAL, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipLOWIndex) + ', ' + str(matrixCracktipLOWIndex) + '\n')
            inp.write('*NSET, NSET=FIBER-CRACKTIPLOW-DISPMEAS, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipFiberDispMeasIndexLOW) + '\n')
            inp.write('*NSET, NSET=MATRIX-CRACKTIPLOW-DISPMEAS, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipMatrixDispMeasIndexLOW) + '\n')
            if 'second' in parameters['mesh']['elements']['order']:
                inp.write('*NSET, NSET=FIBER-NODE-FIRSTBOUNDEDUP, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(fiberFirstBehindCracktipUPIndex) + '\n')
                inp.write('*NSET, NSET=MATRIX-NODE-FIRSTBOUNDEDUP, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(matrixFirstBehindCracktipUPIndex) + '\n')
                inp.write('*NSET, NSET=FIBER-FIRSTBOUNDED-DISPMEASUP, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(firstBehindCracktipFiberDispMeasIndexUP) + '\n')
                inp.write('*NSET, NSET=MATRIX-FIRSTBOUNDED-DISPMEASUP, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(firstBehindCracktipMatrixDispMeasIndexUP) + '\n')
                inp.write('*NSET, NSET=FIBER-NODE-FIRSTBOUNDEDLOW, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(fiberFirstBehindCracktipLOWIndex) + '\n')
                inp.write('*NSET, NSET=MATRIX-NODE-FIRSTBOUNDEDLOW, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(matrixFirstBehindCracktipLOWIndex) + '\n')
                inp.write('*NSET, NSET=FIBER-FIRSTBOUNDED-DISPMEASLOW, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(firstBehindCracktipFiberDispMeasIndexLOW) + '\n')
                inp.write('*NSET, NSET=MATRIX-FIRSTBOUNDED-DISPMEASLOW, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(firstBehindCracktipMatrixDispMeasIndexLOW) + '\n')
                if 'inverseSquareRoot' in parameters['singularity']['type']:
                    inp.write('*NSET, NSET=FIBER-NODE-SECONDBOUNDEDUP, INSTANCE=RVE-assembly' + '\n')
                    inp.write(' ' + str(fiberSecondBehindCracktipUPIndex) + '\n')
                    inp.write('*NSET, NSET=MATRIX-NODE-SECONDBOUNDEDUP, INSTANCE=RVE-assembly' + '\n')
                    inp.write(' ' + str(matrixSecondBehindCracktipUPIndex) + '\n')
                    inp.write('*NSET, NSET=FIBER-NODE-SECONDBOUNDEDLOW, INSTANCE=RVE-assembly' + '\n')
                    inp.write(' ' + str(fiberSecondBehindCracktipLOWIndex) + '\n')
                    inp.write('*NSET, NSET=MATRIX-NODE-SECONDBOUNDEDLOW, INSTANCE=RVE-assembly' + '\n')
                    inp.write(' ' + str(matrixSecondBehindCracktipLOWIndex) + '\n')
            inp.write('*NSET, NSET=CRACKTIPUP-DUMMY-NODE, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipUPDummyIndex) + '\n')
            inp.write('*NSET, NSET=CRACKTIPLOW-DUMMY-NODE, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipLOWDummyIndex) + '\n')
            if 'second' in parameters['mesh']['elements']['order']:
                inp.write('*NSET, NSET=FIRSTBOUNDEDUP-DUMMY-NODE, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(firstBehindCracktipUPDummyIndex) + '\n')
                inp.write('*NSET, NSET=FIRSTBOUNDEDLOW-DUMMY-NODE, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(firstBehindCracktipLOWDummyIndex) + '\n')
                if 'inverseSquareRoot' in parameters['singularity']['type']:
                    inp.write('*NSET, NSET=SECONDBOUNDEDUP-DUMMY-NODE, INSTANCE=RVE-assembly' + '\n')
                    inp.write(' ' + str(secondBehindCracktipUPDummyIndex) + '\n')
                    inp.write('*NSET, NSET=SECONDBOUNDEDLOW-DUMMY-NODE, INSTANCE=RVE-assembly' + '\n')
                    inp.write(' ' + str(secondBehindCracktipLOWDummyIndex) + '\n')
    else:
        with open(modinpfullpath,'a') as inp:
            inp.write('*NSET, NSET=FIBER-CRACKTIP, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipIndex) + '\n')
            inp.write('*NSET, NSET=MATRIX-CRACKTIP, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(matrixCracktipIndex) + '\n')
            inp.write('*NSET, NSET=CRACKTIP-CONTOURINTEGRAL, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipIndex) + ', ' + str(matrixCracktipIndex) + '\n')
            inp.write('*NSET, NSET=FIBER-CRACKTIP-DISPMEAS, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipFiberDispMeasIndex) + '\n')
            inp.write('*NSET, NSET=MATRIX-CRACKTIP-DISPMEAS, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipMatrixDispMeasIndex) + '\n')
            if 'second' in parameters['mesh']['elements']['order']:
                inp.write('*NSET, NSET=FIBER-NODE-FIRSTBOUNDED, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(fiberFirstBehindCracktipIndex) + '\n')
                inp.write('*NSET, NSET=MATRIX-NODE-FIRSTBOUNDED, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(matrixFirstBehindCracktipIndex) + '\n')
                inp.write('*NSET, NSET=FIBER-FIRSTBOUNDED-DISPMEAS, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(firstBehindCracktipFiberDispMeasIndex) + '\n')
                inp.write('*NSET, NSET=MATRIX-FIRSTBOUNDED-DISPMEAS, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(firstBehindCracktipMatrixDispMeasIndex) + '\n')
                if 'inverseSquareRoot' in parameters['singularity']['type']:
                    inp.write('*NSET, NSET=FIBER-NODE-SECONDBOUNDED, INSTANCE=RVE-assembly' + '\n')
                    inp.write(' ' + str(fiberSecondBehindCracktipIndex) + '\n')
                    inp.write('*NSET, NSET=MATRIX-NODE-SECONDBOUNDED, INSTANCE=RVE-assembly' + '\n')
                    inp.write(' ' + str(matrixSecondBehindCracktipIndex) + '\n')
            inp.write('*NSET, NSET=CRACKTIP-DUMMY-NODE, INSTANCE=RVE-assembly' + '\n')
            inp.write(' ' + str(cracktipDummyIndex) + '\n')
            if 'second' in parameters['mesh']['elements']['order']:
                inp.write('*NSET, NSET=FIRSTBOUNDED-DUMMY-NODE, INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(firstBehindCracktipDummyIndex) + '\n')
                if 'inverseSquareRoot' in parameters['singularity']['type']:
                    inp.write('*NSET, NSET=SECONDBOUNDED-DUMMY-NODE, INSTANCE=RVE-assembly' + '\n')
                    inp.write(' ' + str(secondBehindCracktipDummyIndex) + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write right side node sets ...',True)
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=RIGHTSIDE-WITHOUT-CORNERS, INSTANCE=RVE-assembly' + '\n')
        line = ''
        for n,node in enumerate(rightSideWithoutCornersNodeset):
            if n>0 and n%8==0.0:
                line += ' ' + str(node)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(node) + ','
        if len(line)>0:
            inp.write(line + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write left side node sets ...',True)
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=LEFTSIDE-WITHOUT-CORNERS, INSTANCE=RVE-assembly' + '\n')
        line = ''
        for n,node in enumerate(leftSideWithoutCornersNodeset):
            if n>0 and n%8==0.0:
                line += ' ' + str(node)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(node) + ','
        if len(line)>0:
            inp.write(line + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write north side node sets ...',True)
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=SOUTHWEST-CORNER, INSTANCE=RVE-assembly' + '\n')
        inp.write(' ' + str(southwestIndex) + '\n')
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=SOUTHEAST-CORNER, INSTANCE=RVE-assembly' + '\n')
        inp.write(' ' + str(southeastIndex) + '\n')
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=UPPERSIDE-WITHOUT-CORNERS, INSTANCE=RVE-assembly' + '\n')
        line = ''
        for n,node in enumerate(northSideWithoutCornersNodeset):
            if n>0 and n%8==0.0:
                line += ' ' + str(node)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(node) + ','
        if len(line)>0:
            inp.write(line + '\n')
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=UPPERSIDE-WITHOUT-NECORNER, INSTANCE=RVE-assembly' + '\n')
        line = ' ' + str(northwestIndex) + ','
        for n,node in enumerate(northSideWithoutCornersNodeset):
            if (n+1)>0 and (n+1)%8==0.0:
                line += ' ' + str(node)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(node) + ','
        if len(line)>0:
            inp.write(line + '\n')
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=UPPERSIDE-WITHOUT-NWCORNER, INSTANCE=RVE-assembly' + '\n')
        line = ' ' + str(northeastIndex) + ','
        for n,node in enumerate(northSideWithoutCornersNodeset):
            if (n+1)>0 and (n+1)%8==0.0:
                line += ' ' + str(node)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(node) + ','
        if len(line)>0:
            inp.write(line + '\n')
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=NORTHWEST-CORNER, INSTANCE=RVE-assembly' + '\n')
        inp.write(' ' + str(northwestIndex) + '\n')
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=NORTHEAST-CORNER, INSTANCE=RVE-assembly' + '\n')
        inp.write(' ' + str(northeastIndex) + '\n')
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=NORTHSIDE-CENTER, INSTANCE=RVE-assembly' + '\n')
        inp.write(' ' + str(northSideCenter) + '\n')
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=NORTHSIDE-POSSIDE, INSTANCE=RVE-assembly' + '\n')
        line = ''
        for n,node in enumerate(northSidePosSide):
            if n>0 and n%8==0.0:
                line += ' ' + str(node)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(node) + ','
        if len(line)>0:
            inp.write(line + '\n')
    with open(modinpfullpath,'a') as inp:
        inp.write('*NSET, NSET=NORTHSIDE-NEGSIDE, INSTANCE=RVE-assembly' + '\n')
        line = ''
        for n,node in enumerate(northSideNegSide):
            if n>0 and n%8==0.0:
                line += ' ' + str(node)
                inp.write(line + '\n')
                line = ''
            else:
                line += ' ' + str(node) + ','
        if len(line)>0:
            inp.write(line + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    if 'ulinearCoupling' in parameters['BC']['northSide']['type'] or 'vkinCouplingmeanside' in parameters['BC']['northSide']['type']:
        with open(modinpfullpath,'a') as inp:
            for n,node in enumerate(northSideWithoutCornersNodeset):
                inp.write('*NSET, NSET=NORTHSIDE-N'+ str(n+1) +', INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(node) + '\n')
    if 'antisymmetry' in parameters['BC']['northSide']['type']:
        with open(modinpfullpath,'a') as inp:
            for n,node in enumerate(northSidePosSide):
                inp.write('*NSET, NSET=NORTHSIDE-POSSIDE-N'+ str(n+1) +', INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(node) + '\n')
            for n,node in enumerate(northSideNegSide):
                inp.write('*NSET, NSET=NORTHSIDE-NEGSIDE-N'+ str(n+1) +', INSTANCE=RVE-assembly' + '\n')
                inp.write(' ' + str(node) + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write equation definitions ...',True)
    with open(modinpfullpath,'a') as inp:
        inp.write('*EQUATION' + '\n')
        if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
            inp.write(' 3' + '\n')
            inp.write(' FIBER-CRACKTIPUP,1,1,MATRIX-CRACKTIPUP,1,-1,CRACKTIPUP-DUMMY-NODE,1,-1' + '\n')
            inp.write(' 3' + '\n')
            inp.write(' FIBER-CRACKTIPLOW,1,1,MATRIX-CRACKTIPLOW,1,-1,CRACKTIPLOW-DUMMY-NODE,1,-1' + '\n')
            inp.write(' 3' + '\n')
            inp.write(' FIBER-CRACKTIPUP,2,1,MATRIX-CRACKTIPUP,2,-1,CRACKTIPUP-DUMMY-NODE,2,-1' + '\n')
            inp.write(' 3' + '\n')
            inp.write(' FIBER-CRACKTIPLOW,2,1,MATRIX-CRACKTIPLOW,2,-1,CRACKTIPLOW-DUMMY-NODE,2,-1' + '\n')
            if 'second' in parameters['mesh']['elements']['order']:
                inp.write(' 3' + '\n')
                inp.write(' FIBER-NODE-FIRSTBOUNDEDUP,1,1,MATRIX-NODE-FIRSTBOUNDEDUP,1,-1,FIRSTBOUNDEDUP-DUMMY-NODE,1,-1' + '\n')
                inp.write(' 3' + '\n')
                inp.write(' FIBER-NODE-FIRSTBOUNDEDLOW,1,1,MATRIX-NODE-FIRSTBOUNDEDLOW,1,-1,FIRSTBOUNDEDLOW-DUMMY-NODE,1,-1' + '\n')
                inp.write(' 3' + '\n')
                inp.write(' FIBER-NODE-FIRSTBOUNDEDUP,2,1,MATRIX-NODE-FIRSTBOUNDEDUP,2,-1,FIRSTBOUNDEDUP-DUMMY-NODE,2,-1' + '\n')
                inp.write(' 3' + '\n')
                inp.write(' FIBER-NODE-FIRSTBOUNDEDLOW,2,1,MATRIX-NODE-FIRSTBOUNDEDLOW,2,-1,FIRSTBOUNDEDLOW-DUMMY-NODE,2,-1' + '\n')
                if 'inverseSquareRoot' in parameters['singularity']['type']:
                    inp.write(' 3' + '\n')
                    inp.write(' FIBER-NODE-SECONDBOUNDEDUP,1,1,MATRIX-NODE-SECONDBOUNDEDUP,1,-1,SECONDBOUNDEDUP-DUMMY-NODE,1,-1' + '\n')
                    inp.write(' 3' + '\n')
                    inp.write(' FIBER-NODE-SECONDBOUNDEDLOW,1,1,MATRIX-NODE-SECONDBOUNDEDLOW,1,-1,SECONDBOUNDEDLOW-DUMMY-NODE,1,-1' + '\n')
                    inp.write(' 3' + '\n')
                    inp.write(' FIBER-NODE-SECONDBOUNDEDUP,2,1,MATRIX-NODE-SECONDBOUNDEDUP,2,-1,SECONDBOUNDEDUP-DUMMY-NODE,2,-1' + '\n')
                    inp.write(' 3' + '\n')
                    inp.write(' FIBER-NODE-SECONDBOUNDEDLOW,2,1,MATRIX-NODE-SECONDBOUNDEDLOW,2,-1,SECONDBOUNDEDLOW-DUMMY-NODE,2,-1' + '\n')
        else:
            inp.write(' 3' + '\n')
            inp.write(' FIBER-CRACKTIP,1,1,MATRIX-CRACKTIP,1,-1,CRACKTIP-DUMMY-NODE,1,-1' + '\n')
            inp.write(' 3' + '\n')
            inp.write(' FIBER-CRACKTIP,2,1,MATRIX-CRACKTIP,2,-1,CRACKTIP-DUMMY-NODE,2,-1' + '\n')
            if 'second' in parameters['mesh']['elements']['order']:
                inp.write(' 3' + '\n')
                inp.write(' FIBER-NODE-FIRSTBOUNDED,1,1,MATRIX-NODE-FIRSTBOUNDED,1,-1,FIRSTBOUNDED-DUMMY-NODE,1,-1' + '\n')
                inp.write(' 3' + '\n')
                inp.write(' FIBER-NODE-FIRSTBOUNDED,2,1,MATRIX-NODE-FIRSTBOUNDED,2,-1,FIRSTBOUNDED-DUMMY-NODE,2,-1' + '\n')
                if 'inverseSquareRoot' in parameters['singularity']['type']:
                    inp.write(' 3' + '\n')
                    inp.write(' FIBER-NODE-SECONDBOUNDED,1,1,MATRIX-NODE-SECONDBOUNDED,1,-1,SECONDBOUNDED-DUMMY-NODE,1,-1' + '\n')
                    inp.write(' 3' + '\n')
                    inp.write(' FIBER-NODE-SECONDBOUNDED,2,1,MATRIX-NODE-SECONDBOUNDED,2,-1,SECONDBOUNDED-DUMMY-NODE,2,-1' + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    if 'vgeomCoupling' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions on NORTH side ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Chosen boundary condition: geometric coupling',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('*MPC' + '\n')
            inp.write(' SLIDER, UPPERSIDE-WITHOUT-CORNERS, NORTHWEST-CORNER, NORTHEAST-CORNER' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    elif 'vkinrightCoupling' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions on NORTH side ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Chosen boundary condition: kinematic coupling with north-east corner as reference node',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('*KINEMATIC COUPLING, REF NODE = NORTHEAST-CORNER' + '\n')
            inp.write(' UPPERSIDE-WITHOUT-NECORNER, 2' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    elif 'vkinleftCoupling' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions on NORTH side ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Chosen boundary condition: kinematic coupling with north-west corner as reference node',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('*KINEMATIC COUPLING, REF NODE = NORTHWEST-CORNER' + '\n')
            inp.write(' UPPERSIDE-WITHOUT-NWCORNER, 2' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    elif 'vkinCouplingmeancorners' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions on NORTH side ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Chosen boundary condition: nw and ne vertical displacements are set to be equal and all other points are set to this value',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('*EQUATION' + '\n')
            inp.write(' 2' + '\n')
            inp.write(' NORTHWEST-CORNER, 2, 1, NORTHEAST-CORNER, 2, -1' + '\n')
            inp.write(' 3' + '\n')
            inp.write(' UPPERSIDE-WITHOUT-CORNERS, 2, 1, NORTHWEST-CORNER, 2, -0.5, NORTHEAST-CORNER, 2, -0.5' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    elif 'vkinCouplingmeanside' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions on NORTH side ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Chosen boundary condition: mean vertical displacement over all nodes is taken as reference',True)
        with open(modinpfullpath,'a') as inp:
            nEq = len(northSideWithoutCornersNodeset)+2
            inp.write('*EQUATION' + '\n')
            for n in range(0,nEq):
                inp.write(' ' + str(int(nEq)) + '\n')
                line = ''
                for m in range(0,nEq):
                    if m==n:
                        coeff = -nEq*(1.0-1.0/nEq)
                    else:
                        coeff = 1.0
                    if m==0:
                        nodeName = 'NORTHWEST-CORNER'
                    elif m==1:
                        nodeName = 'NORTHEAST-CORNER'
                    else:
                        nodeName = 'NORTHSIDE-N'+ str(m+1-2)
                    line += ' ' + nodeName + ', 2, ' + str(coeff) + ','
                    if m>0 and (m+1)%4==0:
                        line += '\n'
                        inp.write(line)
                        line = ''
                if len(line)>0:
                    line += '\n'
                    inp.write(line)
    elif 'antisymmetry' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions on NORTH side ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Chosen boundary condition: antisymmetry',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('*EQUATION' + '\n')
            for n,node in enumerate(northSidePosSide):
                inp.write(' 3' + '\n')
                inp.write(' NORTHSIDE-POSSIDE-N'+ str(n+1) +', 2, 1, NORTHSIDE-NEGSIDE-N'+ str(n+1) +', 2, 1, NORTHSIDE-CENTER, 2, -2' + '\n')
                inp.write(' 2' + '\n')
                inp.write(' NORTHSIDE-POSSIDE-N'+ str(n+1) +', 1, 1, NORTHSIDE-NEGSIDE-N'+ str(n+1) +', 1, 1' + '\n')
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    if 'ulinearCoupling' in parameters['BC']['northSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions on NORTH side ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Chosen boundary condition: applied linear horizontal displacement',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('*EQUATION' + '\n')
            for n,node in enumerate(northSideWithoutCornersNodeset):
                inp.write(' 2' + '\n')
                inp.write(' NORTHSIDE-N'+ str(n+1) +', 1, 1, NORTHEAST-CORNER, 1, ' + str(-nodes[node][0]/nodes[northeastIndex][0]) + '\n')
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    if 'vkinCouplingmeancorners' in parameters['BC']['rightSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions on RIGHT side ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Chosen boundary condition: ne and se horizontal displacements are set to be equal and all other points are set to this value',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('*EQUATION' + '\n')
            inp.write(' 2' + '\n')
            inp.write(' SOUTHEAST-CORNER, 1, 1, NORTHEAST-CORNER, 1, -1' + '\n')
            inp.write(' 3' + '\n')
            inp.write(' RIGHTSIDE-WITHOUT-CORNERS, 1, 1, SOUTHEAST-CORNER, 1, -0.5, NORTHEAST-CORNER, 1, -0.5' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    if 'vkinCouplingmeancorners' in parameters['BC']['leftSide']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions on LEFT side ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Chosen boundary condition: nw and sw horizontal displacements are set to be equal and all other points are set to this value',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('*EQUATION' + '\n')
            inp.write(' 2' + '\n')
            inp.write(' SOUTHWEST-CORNER, 1, 1, NORTHWEST-CORNER, 1, -1' + '\n')
            inp.write(' 3' + '\n')
            inp.write(' LEFTSIDE-WITHOUT-CORNERS, 1, 1, SOUTHWEST-CORNER, 1, -0.5, NORTHWEST-CORNER, 1, -0.5' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write surface definitions ...',True)
    with open(modinpfullpath,'a') as inp:
        inp.write('*SURFACE, NAME=FiberSurface, TYPE=ELEMENT' + '\n')
        inp.write(' FIBER-CRACKFACE-ELEMENTS' + '\n')
        inp.write('*SURFACE, NAME=MatrixSurface, TYPE=ELEMENT' + '\n')
        inp.write(' MATRIX-CRACKFACE-ELEMENTS' + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write end assembly ...',True)
    with open(modinpfullpath,'a') as inp:
        inp.write('*End Assembly' + '\n')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write contact interaction ...',True)
    with open(modinpfullpath,'a') as inp:
        inp.write('*CONTACT PAIR, INTERACTION=CrackFacesContact, SMALL SLIDING' + '\n')
        inp.write(' MatrixSurface, FiberSurface' + '\n')
        inp.write('*SURFACE INTERACTION, NAME=CrackFacesContact' + '\n')
        inp.write(' 1.0' + '\n')
    if 'static' in parameters['surface']['friction']['type']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Static friction (Coulomb model) is present between crack faces',True)
        with open(modinpfullpath,'a') as inp:
            if 'maxtau' in parameters['surface']['friction']['type']:
                inp.write('*FRICTION, TAUMAX=' + str(parameters['surface']['friction']['maxtau']) + '\n')
                writeLineToLogFile(logfilepath,'a',baselogindent + 5*logindent + 'Maximum tangential stress = ' + str(parameters['surface']['friction']['maxtau']) + '[MPa]',True)
            else:
                inp.write('*FRICTION' + '\n')
            inp.write(' ' + str(parameters['surface']['friction']['static']) + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 5*logindent + 'Static friction coefficient = ' + str(parameters['surface']['friction']['static']) + '[-]',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    if len(parameters['steps'])>1:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
        with open(modinpfullpath,'a') as inp:
            for line in inpfilelines[endAssembly+1:startTempStep+2]:
                inp.write(line)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions for VCCT  ...',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('** BOUNDARY CONDITIONS' + '\n')
            inp.write('**' + '\n')
            inp.write('*BOUNDARY, OP=MOD' + '\n')
            if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
                inp.write(' CRACKTIPUP-DUMMY-NODE, ENCASTRE' + '\n')
                inp.write(' CRACKTIPLOW-DUMMY-NODE, ENCASTRE' + '\n')
                if 'second' in parameters['mesh']['elements']['order']:
                    inp.write(' FIRSTBOUNDEDUP-DUMMY-NODE, ENCASTRE' + '\n')
                    inp.write(' FIRSTBOUNDEDLOW-DUMMY-NODE, ENCASTRE' + '\n')
                    if 'inverseSquareRoot' in parameters['singularity']['type']:
                        inp.write(' SECONDBOUNDEDUP-DUMMY-NODE, ENCASTRE' + '\n')
                        inp.write(' SECONDBOUNDEDLOW-DUMMY-NODE, ENCASTRE' + '\n')
            else:
                inp.write(' CRACKTIP-DUMMY-NODE, ENCASTRE' + '\n')
                if 'second' in parameters['mesh']['elements']['order']:
                    inp.write(' FIRSTBOUNDED-DUMMY-NODE, ENCASTRE' + '\n')
                    if 'inverseSquareRoot' in parameters['singularity']['type']:
                        inp.write(' SECONDBOUNDED-DUMMY-NODE, ENCASTRE' + '\n')
            inp.write('**' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
        with open(modinpfullpath,'a') as inp:
            for line in inpfilelines[startTempStep+2:startTempCI]:
                inp.write(line)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write J-integral over reduced contours  ...',True)
        crackName = inpfilelines[startTempCI].replace('\n','').split(',')[1].split('=')[1]
        nContours = inpfilelines[startTempCI].replace('\n','').split(',')[2].split('=')[1]
        qx = -np.sin(parameters['geometry']['deltatheta']*np.pi/180.0)
        qy = np.cos(parameters['geometry']['deltatheta']*np.pi/180.0)
        with open(modinpfullpath,'a') as inp:
            inp.write('*CONTOUR INTEGRAL, CRACK NAME=' + crackName + ', CONTOURS=' + nContours + '\n')
            inp.write(' ' + 'CRACKTIP-CONTOURINTEGRAL, ' + str(qx) + ', ' + str(qy) + ', 0.0' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
        with open(modinpfullpath,'a') as inp:
            for line in inpfilelines[startTempCI+2:startLoadStep+2]:
                inp.write(line)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write loads  ...',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('** LOADS' + '\n')
            inp.write('**' + '\n')
            for load in parameters['loads'].values():
                if 'appliedUniformPressure' in load['type'] or 'applieduniformpressure' in load['type'] or 'applied Uniform Pressure' in load['type'] or 'applied uniform pressure' in load['type']:
                    inp.write('*DSLOAD, OP=MOD' + '\n')
                    inp.write(' ' + load['set'] + ', P, ' + str(load['value']) + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions for VCCT  ...',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('** BOUNDARY CONDITIONS' + '\n')
            inp.write('**' + '\n')
            inp.write('*BOUNDARY, OP=MOD' + '\n')
            if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
                inp.write(' CRACKTIPUP-DUMMY-NODE, ENCASTRE' + '\n')
                inp.write(' CRACKTIPLOW-DUMMY-NODE, ENCASTRE' + '\n')
                if 'second' in parameters['mesh']['elements']['order']:
                    inp.write(' FIRSTBOUNDEDUP-DUMMY-NODE, ENCASTRE' + '\n')
                    inp.write(' FIRSTBOUNDEDLOW-DUMMY-NODE, ENCASTRE' + '\n')
                    if 'inverseSquareRoot' in parameters['singularity']['type']:
                        inp.write(' SECONDBOUNDEDUP-DUMMY-NODE, ENCASTRE' + '\n')
                        inp.write(' SECONDBOUNDEDLOW-DUMMY-NODE, ENCASTRE' + '\n')
            else:
                inp.write(' CRACKTIP-DUMMY-NODE, ENCASTRE' + '\n')
                if 'second' in parameters['mesh']['elements']['order']:
                    inp.write(' FIRSTBOUNDED-DUMMY-NODE, ENCASTRE' + '\n')
                    if 'inverseSquareRoot' in parameters['singularity']['type']:
                        inp.write(' SECONDBOUNDED-DUMMY-NODE, ENCASTRE' + '\n')
            inp.write('**' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
        with open(modinpfullpath,'a') as inp:
            for line in inpfilelines[startLoadStep+2:startLoadCI]:
                inp.write(line)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write J-integral over reduced contours  ...',True)
        crackName = inpfilelines[startLoadCI].replace('\n','').split(',')[1].split('=')[1]
        nContours = inpfilelines[startLoadCI].replace('\n','').split(',')[2].split('=')[1]
        qx = -np.sin(parameters['geometry']['deltatheta']*np.pi/180.0)
        qy = np.cos(parameters['geometry']['deltatheta']*np.pi/180.0)
        with open(modinpfullpath,'a') as inp:
            inp.write('*CONTOUR INTEGRAL, CRACK NAME=' + crackName + ', CONTOURS=' + nContours + '\n')
            inp.write(' ' + 'CRACKTIP-CONTOURINTEGRAL, ' + str(qx) + ', ' + str(qy) + ', 0.0' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
        with open(modinpfullpath,'a') as inp:
            for line in inpfilelines[startLoadCI+2:]:
                inp.write(line)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    else:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
        with open(modinpfullpath,'a') as inp:
            for line in inpfilelines[endAssembly+1:startBC]:
                inp.write(line)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write loads  ...',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('** LOADS' + '\n')
            inp.write('**' + '\n')
            for load in parameters['loads'].values():
                if 'appliedUniformPressure' in load['type'] or 'applieduniformpressure' in load['type'] or 'applied Uniform Pressure' in load['type'] or 'applied uniform pressure' in load['type']:
                    inp.write('*DSLOAD, OP=MOD' + '\n')
                    inp.write(' ' + load['set'] + ', P, ' + str(load['value']) + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write boundary conditions for VCCT  ...',True)
        with open(modinpfullpath,'a') as inp:
            inp.write('** BOUNDARY CONDITIONS' + '\n')
            inp.write('**' + '\n')
            inp.write('*BOUNDARY, OP=MOD' + '\n')
            if np.abs(theta)>0.0 or 'full' in parameters['geometry']['fiber']['type']:
                inp.write(' CRACKTIPUP-DUMMY-NODE, ENCASTRE' + '\n')
                inp.write(' CRACKTIPLOW-DUMMY-NODE, ENCASTRE' + '\n')
                if 'second' in parameters['mesh']['elements']['order']:
                    inp.write(' FIRSTBOUNDEDUP-DUMMY-NODE, ENCASTRE' + '\n')
                    inp.write(' FIRSTBOUNDEDLOW-DUMMY-NODE, ENCASTRE' + '\n')
                    if 'inverseSquareRoot' in parameters['singularity']['type']:
                        inp.write(' SECONDBOUNDEDUP-DUMMY-NODE, ENCASTRE' + '\n')
                        inp.write(' SECONDBOUNDEDLOW-DUMMY-NODE, ENCASTRE' + '\n')
            else:
                inp.write(' CRACKTIP-DUMMY-NODE, ENCASTRE' + '\n')
                if 'second' in parameters['mesh']['elements']['order']:
                    inp.write(' FIRSTBOUNDED-DUMMY-NODE, ENCASTRE' + '\n')
                    if 'inverseSquareRoot' in parameters['singularity']['type']:
                        inp.write(' SECONDBOUNDED-DUMMY-NODE, ENCASTRE' + '\n')
            inp.write('**' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
        with open(modinpfullpath,'a') as inp:
            for line in inpfilelines[startBC+1:startCI]:
                inp.write(line)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write J-integral over reduced contours  ...',True)
        crackName = inpfilelines[startCI].replace('\n','').split(',')[1].split('=')[1]
        nContours = inpfilelines[startCI].replace('\n','').split(',')[2].split('=')[1]
        qx = -np.sin(parameters['geometry']['deltatheta']*np.pi/180.0)
        qy = np.cos(parameters['geometry']['deltatheta']*np.pi/180.0)
        with open(modinpfullpath,'a') as inp:
            inp.write('*CONTOUR INTEGRAL, CRACK NAME=' + crackName + ', CONTOURS=' + nContours + '\n')
            inp.write(' ' + 'CRACKTIP-CONTOURINTEGRAL, ' + str(qx) + ', ' + str(qy) + ', 0.0' + '\n')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Write from original input file  ...',True)
        with open(modinpfullpath,'a') as inp:
            for line in inpfilelines[endCI+1:]:
                inp.write(line)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    if  parameters['simulation-pipeline']['remove-INP']:
        skipLineToLogFile(logfilepath,'a',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Remove .inp file from working directory... ',True)
        try:
            os.remove(inpfullpath)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        except Exception, error:
            writeErrorToLogFile(logfilepath,'a',Exception,error,True)
            sys.exc_clear()
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    return modinpname

def runRVEsimulation(wd,inpfile,ncpus,logfilepath,baselogindent,logindent):
    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: runRVEsimulation(wd,inpfile,ncpus,logfilepath,baselogindent,logindent)',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Creating and submitting job ...',True)
    try:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create job ' + inpfile.split('.')[0] + ' from input file ' + inpfile,True)
        mdb.JobFromInputFile(name=inpfile.split('.')[0],inputFileName=inpfile,type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=99, memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, userSubroutine='',scratch='', multiprocessingMode=DEFAULT, numCpus=ncpus, numDomains=12,numGPUs=0)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Submit job ...',True)
        mdb.jobs[inpfile.split('.')[0]].submit(consistencyChecking=OFF)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Wait for completion ...',True)
        mdb.jobs[inpfile.split('.')[0]].waitForCompletion()
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    except Exception, error:
        writeErrorToLogFile(logfilepath,'a',Exception,error,True)
        sys.exc_clear()
        if 'Windows' in system():
            writeLineToLogFile(logfilepath,'a',2*logindent + 'Create Windows command file',True)
            cmdfile = join(wd,'executeABAanalysis.cmd')
            with open(cmdfile,'w') as cmd:
                cmd.write('\n')
                cmd.write('CD ' + wd + '\n')
                cmd.write('\n')
                cmd.write('abaqus analysis job=' + inpfile.split('.')[0] + ' interactive cpus=' + str(ncpus) + '\n')
            writeLineToLogFile(logfilepath,'a',2*logindent + 'Executing Windows command file...',True)
            try:
                subprocess.call('cmd.exe /C ' + cmdfile)
                writeLineToLogFile(logfilepath,'a',2*logindent + '... done.',True)
            except Exception,error:
                writeLineToLogFile(logfilepath,'a',2*logindent + 'ERROR',True)
                writeLineToLogFile(logfilepath,'a',2*logindent + str(Exception),True)
                writeLineToLogFile(logfilepath,'a',2*logindent + str(error),True)
                sys.exc_clear()
        elif 'Linux' in system():
            writeLineToLogFile(logfilepath,'a',2*logindent + 'Create Linux bash file',True)
            bashfile = join(wd,'executeABAanalysis.sh')
            with open(bashfile,'w') as bsh:
                bsh.write('#!/bin/bash\n')
                bsh.write('\n')
                bsh.write('cd ' + wd + '\n')
                bsh.write('\n')
                bsh.write('abaqus analysis job=' + inpfile.split('.')[0] + ' interactive cpus=' + str(ncpus) + '\n')
                writeLineToLogFile(logfilepath,'a',2*logindent + 'Executing Linux bash file...',True)
                try:
                    writeLineToLogFile(logfilepath,'a',3*logindent + 'Change permissions to ' + bashfile ,True)
                    os.chmod(bashfile, 0o755)
                    writeLineToLogFile(logfilepath,'a','Run bash file',True)
                    call('.' + bashfile)
                    writeLineToLogFile(logfilepath,'a',2*logindent + '... done.',True)
                except Exception:
                    writeLineToLogFile(logfilepath,'a',2*logindent + 'ERROR',True)
                    writeLineToLogFile(logfilepath,'a',2*logindent + str(Exception),True)
                    writeLineToLogFile(logfilepath,'a',2*logindent + str(error),True)
                    sys.exc_clear()
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Exiting function: runRVEsimulation(wd,inpfile,ncpus,baselogindent,logindent)',True)

def computeVCCT(logfilepath,baselogindent,logindent,odb,step,frame,order,singularity,isPressureLoaded,uniformP,nodesVCCT,phi,Rf,delta,Jintegral):
    results = {}
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Extract forces and displacements ...',True)

    RFcracktip = getFieldOutput(odb,step,frame,'RF',nodesVCCT['cracktipDummyNode'])
    if 'second' in order:
        RFfirstbounded = getFieldOutput(odb,step,frame,'RF',nodesVCCT['firstboundedDummyNode'])
        if 'inverseSquareRoot' in singularity:
            RFsecondbounded = getFieldOutput(odb,step,frame,'RF',nodesVCCT['secondboundedDummyNode'])
    fiberCracktipDisplacement = getFieldOutput(odb,step,frame,'U',nodesVCCT['fiberCracktipDispMeas'])
    matrixCracktipDisplacement = getFieldOutput(odb,step,frame,'U',nodesVCCT['matrixCracktipDispMeas'])
    if 'second' in order:
        fiberFirstboundedDisplacement = getFieldOutput(odb,step,frame,'U',nodesVCCT['fiberFirstboundedDispMeas'])
        matrixFirstboundedDisplacement = getFieldOutput(odb,step,frame,'U',nodesVCCT['matrixFirstboundedDispMeas'])

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Rotate forces and displacements ...',True)

    xRFcracktip = RFcracktip.values[0].data[0]
    yRFcracktip = RFcracktip.values[0].data[1]
    rRFcracktip = np.cos(phi)*xRFcracktip + np.sin(phi)*yRFcracktip
    thetaRFcracktip = -np.sin(phi)*xRFcracktip + np.cos(phi)*yRFcracktip
    if 'second' in order:
        xRFfirstbounded = RFfirstbounded.values[0].data[0]
        yRFfirstbounded = RFfirstbounded.values[0].data[1]
        rRFfirstbounded = np.cos(phi)*xRFfirstbounded + np.sin(phi)*yRFfirstbounded
        thetaRFfirstbounded = -np.sin(phi)*xRFfirstbounded + np.cos(phi)*yRFfirstbounded
        if isPressureLoaded:
            rRFcracktip -= uniformP*(Rf*delta*np.pi/180.0)/6
            rRFfirstbounded -= 2*uniformP*(Rf*delta*np.pi/180.0)/3
        results['xRFfirstbounded'] = xRFfirstbounded
        results['yRFfirstbounded'] = yRFfirstbounded
        results['rRFfirstbounded'] = rRFfirstbounded
        results['thetaRFfirstbounded'] = thetaRFfirstbounded
        if 'inverseSquareRoot' in singularity:
            xRFsecondbounded = RFsecondbounded.values[0].data[0]
            yRFsecondbounded = RFsecondbounded.values[0].data[1]
            rRFsecondbounded = np.cos(phi)*xRFsecondbounded + np.sin(phi)*yRFsecondbounded
            thetaRFsecondbounded = -np.sin(phi)*xRFsecondbounded + np.cos(phi)*yRFsecondbounded
            results['xRFsecondbounded'] = xRFsecondbounded
            results['yRFsecondbounded'] = yRFsecondbounded
            results['rRFsecondbounded'] = rRFsecondbounded
            results['thetaRFsecondbounded'] = thetaRFsecondbounded
    else:
        if isPressureLoaded:
            rRFcracktip -= uniformP*(Rf*delta*np.pi/180.0)/2
    results['xRFcracktip'] = xRFcracktip
    results['yRFcracktip'] = yRFcracktip
    results['rRFcracktip'] = rRFcracktip
    results['thetaRFcracktip'] = thetaRFcracktip


    xfiberCracktipDisplacement = fiberCracktipDisplacement.values[0].data[0]
    yfiberCracktipDisplacement = fiberCracktipDisplacement.values[0].data[1]
    rfiberCracktipDisplacement = np.cos(phi)*xfiberCracktipDisplacement + np.sin(phi)*yfiberCracktipDisplacement
    thetafiberCracktipDisplacement = -np.sin(phi)*xfiberCracktipDisplacement + np.cos(phi)*yfiberCracktipDisplacement
    xmatrixCracktipDisplacement = matrixCracktipDisplacement.values[0].data[0]
    ymatrixCracktipDisplacement = matrixCracktipDisplacement.values[0].data[1]
    rmatrixCracktipDisplacement = np.cos(phi)*xmatrixCracktipDisplacement + np.sin(phi)*ymatrixCracktipDisplacement
    thetamatrixCracktipDisplacement = -np.sin(phi)*xmatrixCracktipDisplacement + np.cos(phi)*ymatrixCracktipDisplacement
    results['xfiberCracktipDisplacement'] = xfiberCracktipDisplacement
    results['yfiberCracktipDisplacement'] = yfiberCracktipDisplacement
    results['rfiberCracktipDisplacement'] = rfiberCracktipDisplacement
    results['thetafiberCracktipDisplacement'] = thetafiberCracktipDisplacement
    results['xmatrixCracktipDisplacement'] = xmatrixCracktipDisplacement
    results['ymatrixCracktipDisplacement'] = ymatrixCracktipDisplacement
    results['rmatrixCracktipDisplacement'] = rmatrixCracktipDisplacement
    results['thetamatrixCracktipDisplacement'] = thetamatrixCracktipDisplacement
    if 'second' in order:
        xfiberFirstboundedDisplacement = fiberFirstboundedDisplacement.values[0].data[0]
        yfiberFirstboundedDisplacement = fiberFirstboundedDisplacement.values[0].data[1]
        rfiberFirstboundedDisplacement = np.cos(phi)*xfiberFirstboundedDisplacement + np.sin(phi)*yfiberFirstboundedDisplacement
        thetafiberFirstboundedDisplacement = -np.sin(phi)*xfiberFirstboundedDisplacement + np.cos(phi)*yfiberFirstboundedDisplacement
        xmatrixFirstboundedDisplacement = matrixFirstboundedDisplacement.values[0].data[0]
        ymatrixFirstboundedDisplacement = matrixFirstboundedDisplacement.values[0].data[1]
        rmatrixFirstboundedDisplacement = np.cos(phi)*xmatrixFirstboundedDisplacement + np.sin(phi)*ymatrixFirstboundedDisplacement
        thetamatrixFirstboundedDisplacement = -np.sin(phi)*xmatrixFirstboundedDisplacement + np.cos(phi)*ymatrixFirstboundedDisplacement
        results['xfiberFirstboundedDisplacement'] = xfiberFirstboundedDisplacement
        results['yfiberFirstboundedDisplacement'] = yfiberFirstboundedDisplacement
        results['rfiberFirstboundedDisplacement'] = rfiberFirstboundedDisplacement
        results['thetafiberFirstboundedDisplacement'] = thetafiberFirstboundedDisplacement
        results['xmatrixFirstboundedDisplacement'] = xmatrixFirstboundedDisplacement
        results['ymatrixFirstboundedDisplacement'] = ymatrixFirstboundedDisplacement
        results['rmatrixFirstboundedDisplacement'] = rmatrixFirstboundedDisplacement
        results['thetamatrixFirstboundedDisplacement'] = thetamatrixFirstboundedDisplacement

    xcracktipDisplacement = xmatrixCracktipDisplacement - xfiberCracktipDisplacement
    ycracktipDisplacement = ymatrixCracktipDisplacement - yfiberCracktipDisplacement
    rcracktipDisplacement = rmatrixCracktipDisplacement - rfiberCracktipDisplacement
    thetacracktipDisplacement = thetamatrixCracktipDisplacement - thetafiberCracktipDisplacement
    results['xcracktipDisplacement'] = xcracktipDisplacement
    results['ycracktipDisplacement'] = ycracktipDisplacement
    results['rcracktipDisplacement'] = rcracktipDisplacement
    results['thetacracktipDisplacement'] = thetacracktipDisplacement
    if 'second' in order:
        xfirstboundedDisplacement = xmatrixFirstboundedDisplacement - xfiberFirstboundedDisplacement
        yfirstboundedDisplacement = ymatrixFirstboundedDisplacement - yfiberFirstboundedDisplacement
        rfirstboundedDisplacement = rmatrixFirstboundedDisplacement - rfiberFirstboundedDisplacement
        thetafirstboundedDisplacement = thetamatrixFirstboundedDisplacement - thetafiberFirstboundedDisplacement
        results['xfirstboundedDisplacement'] = xfirstboundedDisplacement
        results['yfirstboundedDisplacement'] = yfirstboundedDisplacement
        results['rfirstboundedDisplacement'] = rfirstboundedDisplacement
        results['thetafirstboundedDisplacement'] = thetafirstboundedDisplacement

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Compute VCCT with GTOT=GI+GII ...',True)

    if 'second' in order:
        if 'inverseSquareRoot' in singularity:
            t11 = 14.0-33.0*np.pi/8.0
            t12 = -52.0+33.0*np.pi/2.0
            t21 = -7.0/2.0+21.0*np.pi/16.0
            t22 = 17.0-21.0*np.pi/4.0
            t31 = 8.0-21.0*np.pi/8.0
            t32 = -32.0+21.0*np.pi/2.0
            GI = np.abs(0.5*(rRFcracktip*(t11*rcracktipDisplacement+t12*rfirstboundedDisplacement)+rRFfirstbounded*(t21*rcracktipDisplacement+t22*rfirstboundedDisplacement)+rRFsecondbounded*(t31*rcracktipDisplacement+t32*rfirstboundedDisplacement))/(Rf*delta*np.pi/180.0))
            GII = np.abs(0.5*(rRFcracktip*(t11*thetacracktipDisplacement+t12*thetafirstboundedDisplacement)+thetaRFfirstbounded*(t21*thetacracktipDisplacement+t22*thetafirstboundedDisplacement)+thetaRFsecondbounded*(t31*thetacracktipDisplacement+t32*thetafirstboundedDisplacement))/(Rf*delta*np.pi/180.0))
        else:
            GI = np.abs(0.5*(rRFcracktip*rcracktipDisplacement+rRFfirstbounded*rfirstboundedDisplacement)/(Rf*delta*np.pi/180.0))
            GII = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement+thetaRFfirstbounded*thetafirstboundedDisplacement)/(Rf*delta*np.pi/180.0))
            GTOTequiv = np.abs(0.5*(xRFcracktip*xcracktipDisplacement+yRFcracktip*ycracktipDisplacement+xRFfirstbounded*xfirstboundedDisplacement+yRFfirstbounded*yfirstboundedDisplacement)/(Rf*delta*np.pi/180.0))
    else:
        GI = np.abs(0.5*(rRFcracktip*rcracktipDisplacement)/(Rf*delta*np.pi/180.0))
        GII = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement)/(Rf*delta*np.pi/180.0))
        GTOTequiv = np.abs(0.5*(xRFcracktip*xcracktipDisplacement+yRFcracktip*ycracktipDisplacement)/(Rf*delta*np.pi/180.0))

    GTOT = GI + GII

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Compute VCCT with GI=GTOT-GII ...',True)

    if 'second' in parameters['mesh']['elements']['order']:
        GIIv2 = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement+thetaRFfirstbounded*thetafirstboundedDisplacement)/(Rf*delta*np.pi/180.0))
    else:
        GIIv2 = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement)/(Rf*delta*np.pi/180.0))

    GTOTv2 = Jintegral

    GIv2 = GTOTv2 - GIIv2

    results['GI'] = GI
    results['GII'] = GII
    results['GTOT'] = GTOT
    results['GTOTequiv'] = GTOTequiv
    results['GIv2'] = GIv2
    results['GIIv2'] = GIIv2
    results['GTOTv2'] = GTOTv2

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + '... done.',True)

    return results

def analyzeRVEresults(odbname,parameters,logfilepath,baselogindent,logindent):

    skipLineToLogFile(logfilepath,'a',True)
    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'In function: analyzeRVEresults(wd,odbname)',True)

    wd = parameters['input']['wd']

    if len(parameters['steps'])>1:
        initialStep = -2
    else:
        initialStep = -1
    #=======================================================================
    # BEGIN - extract performances
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Extract performances...',True)
    try:
        appendCSVfile(parameters['output']['global']['directory'],parameters['output']['global']['filenames']['performances'],[getPerfs(wd,[odbname.split('.')[0]],logfilepath,baselogindent + 2*logindent,logindent)[1]])
    except Exception,e:
        writeErrorToLogFile(logfilepath,'a',Exception,e,True)
        sys.exc_clear()
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - extract performances
    #=======================================================================

    #=======================================================================
    # BEGIN - extract J-integral results
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Extracting J-integral results ...',True)

    if parameters['simulation-pipeline']['analysis']['report-energyreleaserates']:
        if len(parameters['steps'])>1:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '--> THERMAL STEP <--',True)
            try:
                Jintegrals = getJintegrals(wd,odbname.split('.')[0],parameters['Jintegral']['numberOfContours'],1)
            except Exception,e:
                writeErrorToLogFile(logfilepath,'a',Exception,e,True)
                sys.exc_clear()
            JintegralsWithDistance = []
            for v,value in enumerate(Jintegrals):
                JintegralsWithDistance.append([v+1,(v+1)*parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0,value])
            createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['thermalJintegral'],'CONTOUR, AVERAGE DISTANCE, GTOT')
            appendCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['thermalJintegral'],JintegralsWithDistance)
            del JintegralsWithDistance
            thermalJintegrals = Jintegrals
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '--> MECHANICAL STEP <--',True)
            try:
                Jintegrals = getJintegrals(wd,odbname.split('.')[0],parameters['Jintegral']['numberOfContours'],2)
            except Exception,e:
                writeErrorToLogFile(logfilepath,'a',Exception,e,True)
                sys.exc_clear()
            JintegralsWithDistance = []
            for v,value in enumerate(Jintegrals):
                JintegralsWithDistance.append([v+1,(v+1)*parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0,value])
            createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['Jintegral'],'CONTOUR, AVERAGE DISTANCE, GTOT')
            appendCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['Jintegral'],JintegralsWithDistance)
            del JintegralsWithDistance
        else:
            try:
                Jintegrals = getJintegrals(wd,odbname.split('.')[0],parameters['Jintegral']['numberOfContours'],1)
            except Exception,e:
                writeErrorToLogFile(logfilepath,'a',Exception,e,True)
                sys.exc_clear()
            JintegralsWithDistance = []
            for v,value in enumerate(Jintegrals):
                JintegralsWithDistance.append([v+1,(v+1)*parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0,value])
            createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['Jintegral'],'CONTOUR, AVERAGE DISTANCE, GTOT')
            appendCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['Jintegral'],JintegralsWithDistance)
            del JintegralsWithDistance
    else:
        createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['Jintegral'],'CONTOUR, AVERAGE DISTANCE, GTOT')
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - extract J-integral results
    #=======================================================================

    #=======================================================================
    # BEGIN - open ODB
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Opening ODB database ' + odbname + ' in directory ' + wd + ' ...',True)
    if '.odb' not in odbname:
        odbname += '.odb'
    odbfullpath = join(wd,odbname)
    odb = openOdb(path=odbfullpath, readOnly=True)
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - open ODB
    #=======================================================================

    #=======================================================================
    # BEGIN - extract node sets
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Extracting node sets ...',True)

    lowerSide = getSingleNodeSet(odb,'RVE-ASSEMBLY','LOWERSIDE')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- LOWERSIDE',True)

    rightSide = getSingleNodeSet(odb,'RVE-ASSEMBLY','RIGHTSIDE')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- RIGHTSIDE',True)

    thirdCircle = getSingleNodeSet(odb,'RVE-ASSEMBLY','THIRDCIRCLE')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- THIRDCIRCLE',True)

    fiberCrackfaceNodes = getSingleNodeSet(odb,None,'FIBER-CRACKFACE-NODES')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- FIBER-CRACKFACE-NODES',True)

    matrixCrackfaceNodes = getSingleNodeSet(odb,None,'MATRIX-CRACKFACE-NODES')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- MATRIX-CRACKFACE-NODES',True)

    fiberCracktip = getSingleNodeSet(odb,None,'FIBER-CRACKTIP')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- FIBER-CRACKTIP',True)

    cracktipDummyNode = getSingleNodeSet(odb,None,'CRACKTIP-DUMMY-NODE')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- CRACKTIP-DUMMY-NODE',True)

    fiberCracktipDispMeas = getSingleNodeSet(odb,None,'FIBER-CRACKTIP-DISPMEAS')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- FIBER-CRACKTIP-DISPMEAS',True)

    matrixCracktipDispMeas = getSingleNodeSet(odb,None,'MATRIX-CRACKTIP-DISPMEAS')
    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- MATRIX-CRACKTIP-DISPMEAS',True)

    if 'second' in parameters['mesh']['elements']['order']:
        firstboundedDummyNode = getSingleNodeSet(odb,None,'FIRSTBOUNDED-DUMMY-NODE')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- FIRSTBOUNDED-DUMMY-NODE',True)

        fiberFirstboundedDispMeas = getSingleNodeSet(odb,None,'FIBER-FIRSTBOUNDED-DISPMEAS')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- FIBER-FIRSTBOUNDED-DISPMEAS',True)

        matrixFirstboundedDispMeas = getSingleNodeSet(odb,None,'MATRIX-FIRSTBOUNDED-DISPMEAS')
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '-- MATRIX-FIRSTBOUNDED-DISPMEAS',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - extract node sets
    #=======================================================================

    #=======================================================================
    # BEGIN - extract stresses at the boundary
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Extracting stresses at the boundary ...',True)

    # writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract stresses along the right side ...',True)
    # rightsideStress = getFieldOutput(odb,-1,-1,'S',rightSide,3)
    # writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    # writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract deformed coordinates along the right side ...',True)
    # rightsideDefcoords = getFieldOutput(odb,-1,-1,'COORD',rightSide)
    # writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    if parameters['simulation-pipeline']['analysis']['report-stressesatboundary']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract undeformed coordinates along the right side ...',True)
        rightsideUndefcoords = getFieldOutput(odb,initialStep,0,'COORD',rightSide)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Pair data: x0, y0, x, y, sigma_xx, sigma_zz, sigma_yy, tau_xz ...',True)
        rightsideStressdata = []
        for value in rightsideUndefcoords.values:
            node = odb.rootAssembly.instances['RVE-ASSEMBLY'].getNodeFromLabel(value.nodeLabel)
            stress = getFieldOutput(odb,-1,-1,'S',node,3)
            defcoords = getFieldOutput(odb,-1,-1,'COORD',node)
            rightsideStressdata.append([value.data[0],value.data[1],defcoords.values[0].data[0],defcoords.values[0].data[1],stress.values[0].data[0],stress.values[0].data[1],stress.values[0].data[2],stress.values[0].data[3]])
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute minimum, maximum and mean stress ...',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Initialize variables...',True)
        maxSigmaxx = rightsideStressdata[0][4]
        minSigmaxx = rightsideStressdata[0][4]
        meanSigmaxx = 0.0
        weightmeanSigmaxx = 0.0
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '...done.',True)
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Start for loop...',True)
        for s,stress in enumerate(rightsideStressdata):
            if s>0:
                weightmeanSigmaxx += (stress[1]-rightsideStressdata[s-1][1])*(stress[4]+rightsideStressdata[s-1][4])
            meanSigmaxx += stress[4]
            if stress[4]>maxSigmaxx:
                maxSigmaxx = stress[4]
            elif stress[4]<minSigmaxx:
                minSigmaxx = stress[4]
        writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '...done.',True)
        meanSigmaxx /= len(rightsideStressdata)
        weightmeanSigmaxx /= 2*parameters['geometry']['L']
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        if parameters['simulation-pipeline']['analysis']['report-stressesatboundary']:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute normalized coordinates and axial stress ...',True)
            for s,stress in enumerate(rightsideStressdata):
                stress.append(stress[1]/parameters['geometry']['L'])
                stress.append(stress[4]/maxSigmaxx)
                stress.append(stress[4]/minSigmaxx)
                stress.append(stress[4]/meanSigmaxx)
                stress.append(stress[4]/weightmeanSigmaxx)
                rightsideStressdata[s] = stress
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Save data to csv file ...',True)
            rightsideStressdata = np.array(rightsideStressdata)
            rightsideStressdata = rightsideStressdata[np.argsort(rightsideStressdata[:,1])]
            createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['stressesatboundary'],'x0 [um], y0 [um], x [um], y [um], sigma_xx [MPa], sigma_zz [MPa], sigma_yy [MPa], tau_xz [MPa], y0/L [-],  sigma_xx/max(sigma_xx) [-],  sigma_xx/min(sigma_xx) [-],  sigma_xx/avg(sigma_xx) [-],  sigma_xx/weightavg(sigma_xx) [-]')
            appendCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['stressesatboundary'],rightsideStressdata)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
        else:
            createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['stressesatboundary'],'x0 [um], y0 [um], x [um], y [um], sigma_xx [MPa], sigma_zz [MPa], sigma_yy [MPa], tau_xz [MPa], y0/L [-],  sigma_xx/max(sigma_xx) [-],  sigma_xx/min(sigma_xx) [-],  sigma_xx/avg(sigma_xx) [-],  sigma_xx/weightavg(sigma_xx) [-]')
        del rightsideStressdata
        # del rightsideStress
        # del rightsideDefcoords
        del rightsideUndefcoords
    else:
        createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['stressesatboundary'],'x0 [um], y0 [um], x [um], y [um], sigma_xx [MPa], sigma_zz [MPa], sigma_yy [MPa], tau_xz [MPa], y0/L [-],  sigma_xx/max(sigma_xx) [-],  sigma_xx/min(sigma_xx) [-],  sigma_xx/avg(sigma_xx) [-],  sigma_xx/weightavg(sigma_xx) [-]')

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - extract stresses at the boundary
    #=======================================================================

    #=======================================================================
    # BEGIN - extract stresses along symmetry line
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Extracting stresses along symmetry line ...',True)

    if parameters['simulation-pipeline']['analysis']['report-stressesatsymmetryline']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract undeformed coordinates along symmetry line ...',True)
        lowersideUndefcoords = getFieldOutput(odb,initialStep,0,'COORD',lowerSide)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Pair data: x0, y0, x0/Rf, x, y, x/Rf, sigma_xx, sigma_zz, sigma_yy, tau_xz ...',True)
        lowersideStressdata = []
        for value in lowersideUndefcoords.values:
            node = odb.rootAssembly.instances['RVE-ASSEMBLY'].getNodeFromLabel(value.nodeLabel)
            stress = getFieldOutput(odb,-1,-1,'S',node,3)
            defcoords = getFieldOutput(odb,-1,-1,'COORD',node)
            lowersideStressdata.append([value.data[0],value.data[1],value.data[0]/parameters['geometry']['Rf'],defcoords.values[0].data[0],defcoords.values[0].data[1],defcoords.values[0].data[0]/parameters['geometry']['Rf'],stress.values[0].data[0],stress.values[0].data[1],stress.values[0].data[2],stress.values[0].data[3]])
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Save data to csv file ...',True)
        lowersideStressdata = np.array(lowersideStressdata)
        lowersideStressdata = lowersideStressdata[np.argsort(lowersideStressdata[:,0])]
        createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['stressesatsymmetryline'],'x0 [um], y0 [um], x0/Rf [-], x [um], y [um], x/Rf [-], sigma_xx [MPa], sigma_zz [MPa], sigma_yy [MPa], tau_xz [MPa]')
        appendCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['stressesatsymmetryline'],lowersideStressdata)
        del lowersideStressdata
        del lowersideUndefcoords
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
    else:
        createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['stressesatsymmetryline'],'x0 [um], y0 [um], x0/Rf [-], x [um], y [um], x/Rf [-], sigma_xx [MPa], sigma_zz [MPa], sigma_yy [MPa], tau_xz [MPa]')

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - extract stresses along symmetry line
    #=======================================================================

    #=======================================================================
    # BEGIN - extract stresses along radial paths
    #=======================================================================

    if 'report-stressesradialpaths' in parameters['simulation-pipeline']['analysis'].keys():
        if parameters['simulation-pipeline']['analysis']['report-stressesradialpaths']['start']:
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Extracting stresses along radial paths ...',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Open odb session...',True)
            sessionOdb = session.openOdb(name=odbfullpath)
            session.viewports['Viewport: 1'].setValues(displayedObject=sessionOdb)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Determine path variable values ...',True)
            pathAngles = np.arange(parameters['simulation-pipeline']['analysis']['report-stressesradialpaths']['startParameter'],parameters['simulation-pipeline']['analysis']['report-stressesradialpaths']['endParameter'],parameters['simulation-pipeline']['analysis']['report-stressesradialpaths']['stepParameter'])
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create .csv file...',True)
            csvFilename = parameters['output']['local']['directory'].replace('\\','/').split('/')[-1] + '-stressesradialpaths'
            createCSVfile(parameters['output']['local']['directory'],csvFilename,'VARIABLE, angle [°], Ri, Rf, FOLDER, FILENAME')
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)
            nSegsOnPath = int(parameters['simulation-pipeline']['analysis']['report-stressesradialpaths']['nSegsOnPath'])
            for angleNum,pathAngle in enumerate(pathAngles):
                if pathAngle<45.0:
                    pathRadius = parameters['geometry']['L']/np.cos(pathAngle*np.pi/180.0)
                elif pathAngle<90.0:
                    pathRadius = parameters['geometry']['L']/np.cos((90.0-pathAngle)*np.pi/180.0)
                elif pathAngle<135.0:
                    pathRadius = parameters['geometry']['L']/np.cos((pathAngle-90.0)*np.pi/180.0)
                else:
                    pathRadius = parameters['geometry']['L']/np.cos((180.0-pathAngle)*np.pi/180.0)
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Create radial path with min radius ' + str(parameters['geometry']['Rf']) + ' [mum]',True)
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '                        max radius ' + str(pathRadius) + ' [mum]',True)
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '                        orientation ' + str(pathAngle) + ' deg',True)
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '                        number of segments ' + str(nSegsOnPath),True)
                session.Path(name='RadPath-Ang' + str(pathAngle), type=RADIAL, expression=((0, 0, 0), (0, 0, 1), (pathRadius,0, 0)), circleDefinition=ORIGIN_AXIS, numSegments=nSegsOnPath, radialAngle=pathAngle, startRadius=parameters['geometry']['Rf'], endRadius=CIRCLE_RADIUS)
                radpath = session.paths['RadPath-Ang' + str(pathAngle)]
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract stress components...',True)
                # sigmaxx
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_xx',True)
                sigmaxx = xyPlot.XYDataFromPath(path=radpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S11' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmaxx-RadPath-Ang' + str(pathAngle) + '.dat'),xyData=sigmaxx,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S11 [MPa]',str(pathAngle),str(parameters['geometry']['Rf']),str(pathRadius),parameters['output']['local']['directory'],'sigmaxx-RadPath-Ang' + str(pathAngle) + '.dat']])
                # sigmayy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_yy',True)
                sigmayy = xyPlot.XYDataFromPath(path=radpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S22' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmayy-RadPath-Ang' + str(pathAngle) + '.dat'),xyData=sigmayy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S22 [MPa]',str(pathAngle),str(parameters['geometry']['Rf']),str(pathRadius),parameters['output']['local']['directory'],'sigmayy-RadPath-Ang' + str(pathAngle) + '.dat']])
                # tauxy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- tau_xy',True)
                tauxy = xyPlot.XYDataFromPath(path=radpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S12' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauxy-RadPath-Ang' + str(pathAngle) + '.dat'),xyData=tauxy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S12 [MPa]',str(pathAngle),str(parameters['geometry']['Rf']),str(pathRadius),parameters['output']['local']['directory'],'tauxy-RadPath-Ang' + str(pathAngle) + '.dat']])
                # sigmazz
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_zz',True)
                sigmazz = xyPlot.XYDataFromPath(path=radpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S33' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmazz-RadPath-Ang' + str(pathAngle) + '.dat'),xyData=sigmazz,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S33 [MPa]',str(pathAngle),str(parameters['geometry']['Rf']),str(pathRadius),parameters['output']['local']['directory'],'sigmazz-RadPath-Ang' + str(pathAngle) + '.dat']])
                # tauzx
                #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- tau_zx',True)
                #tauzx = xyPlot.XYDataFromPath(path=radpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S13' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauzx-RadPath-Ang' + str(pathAngle) + '.dat'),xyData=tauzx,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S13 [MPa]',str(pathAngle),str(parameters['geometry']['Rf']),str(pathRadius),parameters['output']['local']['directory'],'tauzx-RadPath-Ang' + str(pathAngle) + '.dat']])
                # tauyz
                #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- tau_yz',True)
                #tauyz = xyPlot.XYDataFromPath(path=radpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S23' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauyz-RadPath-Ang' + str(pathAngle) + '.dat'),xyData=tauyz,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S23 [MPa]',str(pathAngle),str(parameters['geometry']['Rf']),str(pathRadius),parameters['output']['local']['directory'],'tauyz-RadPath-Ang' + str(pathAngle) + '.dat']])
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '...done.',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #=======================================================================
    # END - extract stresses along radial paths
    #=======================================================================

    #=======================================================================
    # BEGIN - extract stresses along circumferential paths
    #=======================================================================

    if 'report-stressescircumferentialpaths' in parameters['simulation-pipeline']['analysis'].keys():
        if parameters['simulation-pipeline']['analysis']['report-stressescircumferentialpaths']['start']:
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Extracting stresses along circumferential paths ...',True)
            sessionOdb = session.openOdb(name=odbfullpath)
            session.viewports['Viewport: 1'].setValues(displayedObject=sessionOdb)
            pathRsInt = np.linspace(parameters['geometry']['Rf'],parameters['geometry']['L'],parameters['simulation-pipeline']['analysis']['report-stressescircumferentialpaths']['stepParameter'],endpoint=True)
            pathRsExt = np.linspace(parameters['geometry']['L'],np.sqrt(2)*parameters['geometry']['L'],parameters['simulation-pipeline']['analysis']['report-stressescircumferentialpaths']['stepParameter'],endpoint=False)[1:]
            csvFilename = parameters['output']['local']['directory'].replace('\\','/').split('/')[-1] + '-stressescircumferentialpaths'
            createCSVfile(parameters['output']['local']['directory'],csvFilename,'VARIABLE, R, angle_i [°], angle_f [°], FOLDER, FILENAME')
            nSegsOnPath = int(parameters['simulation-pipeline']['analysis']['report-stressescircumferentialpaths']['nSegsOnPath'])
            for rNum,pathR in enumerate(pathRsInt):
                session.Path(name='CircPath-R' + str(pathR).replace('.','_'), type=CIRCUMFERENTIAL, expression=((0, 0, 0), (0, 0, 1), (pathR, 0, 0)), circleDefinition=ORIGIN_AXIS, numSegments=nSegsOnPath, startAngle=0, endAngle=180, radius=CIRCLE_RADIUS)
                circpath = session.paths['CircPath-R' + str(pathR).replace('.','_')]
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract stress components...',True)
                # sigmaxx
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_xx',True)
                sigmaxx = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S11' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmaxx-CircPath-R' + str(pathR).replace('.','_') + '.dat'),xyData=sigmaxx,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S11 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'sigmaxx-CircPath-R' + str(pathR).replace('.','_') + '.dat']])
                # sigmayy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_yy',True)
                sigmayy = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S22' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmayy-CircPath-R' + str(pathR).replace('.','_') + '.dat'),xyData=sigmayy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S22 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'sigmayy-CircPath-R' + str(pathR).replace('.','_') + '.dat']])
                # tauxy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- tau_xy',True)
                tauxy = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S12' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauxy-CircPath-R' + str(pathR).replace('.','_') + '.dat'),xyData=tauxy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S12 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'tauxy-CircPath-R' + str(pathR).replace('.','_') + '.dat']])
                # sigmazz
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_zz',True)
                sigmazz = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S33' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmazz-CircPath-R' + str(pathR).replace('.','_') + '.dat'),xyData=sigmazz,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S33 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'sigmazz-CircPath-R' + str(pathR).replace('.','_') + '.dat']])
                # tauzx
                #tauzx = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S13' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauzx-CircPath-R' + str(pathR).replace('.','_') + '.dat'),xyData=tauzx,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S13 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'tauzx-CircPath-R' + str(pathR).replace('.','_') + '.dat']])
                # tauyz
                #tauyz = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S23' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauyz-CircPath-R' + str(pathR).replace('.','_') + '.dat'),xyData=tauyz,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S23 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'tauyz-CircPath-R' + str(pathR).replace('.','_') + '.dat']])
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
            for rNum,pathR in enumerate(pathRsExt):
                angleStart1 = np.ceil(np.arccos(parameters['geometry']['L']/pathR)*180.0/np.pi)
                angleStart2 = 90.0-angleStart1
                angleStart3 = 90.0+angleStart1
                angleStart4 = 180.0-angleStart1
                session.Path(name='CircPath-R' + str(pathR).replace('.','_') + 'East' , type=CIRCUMFERENTIAL, expression=((0, 0, 0), (0, 0, 1), (pathR, 0, 0)), circleDefinition=ORIGIN_AXIS, numSegments=nSegsOnPath, startAngle=angleStart1, endAngle=angleStart2, radius=CIRCLE_RADIUS)
                session.Path(name='CircPath-R' + str(pathR).replace('.','_') + 'West' , type=CIRCUMFERENTIAL, expression=((0, 0, 0), (0, 0, 1), (pathR, 0, 0)), circleDefinition=ORIGIN_AXIS, numSegments=nSegsOnPath, startAngle=angleStart3, endAngle=angleStart4, radius=CIRCLE_RADIUS)
                circpath = session.paths['CircPath-R' + str(pathR).replace('.','_') + 'East']
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract stress components...',True)
                # sigmaxx
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_xx',True)
                sigmaxx = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S11' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmaxx-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat'),xyData=sigmaxx,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S11 [MPa]',str(pathRadius),str(angleStart1),str(angleStart2),parameters['output']['local']['directory'],'sigmaxx-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat']])
                # sigmayy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_yy',True)
                sigmayy = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S22' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmayy-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat'),xyData=sigmayy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S22 [MPa]',str(pathRadius),str(angleStart1),str(angleStart2),parameters['output']['local']['directory'],'sigmayy-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat']])
                # tauxy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- tau_xy',True)
                tauxy = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S12' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauxy-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat'),xyData=tauxy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S12 [MPa]',str(pathRadius),str(angleStart1),str(angleStart2),parameters['output']['local']['directory'],'tauxy-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat']])
                # sigmazz
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_zz',True)
                sigmazz = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S33' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmazz-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat'),xyData=sigmazz,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S33 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'sigmazz-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat']])
                # tauzx
                #tauzx = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S13' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauzx-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat'),xyData=tauzx,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S13 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'tauzx-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat']])
                # tauyz
                #tauyz = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S23' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauyz-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat'),xyData=tauyz,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S23 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'tauyz-CircPath-R' + str(pathR).replace('.','_') + 'East' + '.dat']])
                #
                circpath = session.paths['CircPath-R' + str(pathR).replace('.','_') + 'West']
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract stress components...',True)
                # sigmaxx
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_xx',True)
                sigmaxx = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S11' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmaxx-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat'),xyData=sigmaxx,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S11 [MPa]',str(pathRadius),str(angleStart3),str(angleStart4),parameters['output']['local']['directory'],'sigmaxx-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat']])
                # sigmayy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_yy',True)
                sigmayy = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S22' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmayy-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat'),xyData=sigmayy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S22 [MPa]',str(pathRadius),str(angleStart3),str(angleStart4),parameters['output']['local']['directory'],'sigmayy-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat']])
                # tauxy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- tau_xy',True)
                tauxy = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S12' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauxy-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat'),xyData=tauxy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S12 [MPa]',str(pathRadius),str(angleStart3),str(angleStart4),parameters['output']['local']['directory'],'tauxy-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat']])
                # sigmazz
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_zz',True)
                sigmazz = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S33' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmazz-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat'),xyData=sigmazz,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S33 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'sigmazz-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat']])
                # tauzx
                #tauzx = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S13' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauzx-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat'),xyData=tauzx,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S13 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'tauzx-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat']])
                # tauyz
                #tauyz = xyPlot.XYDataFromPath(path=circpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S23' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauyz-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat'),xyData=tauyz,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S23 [MPa]',str(pathRadius),str(0),str(180),parameters['output']['local']['directory'],'tauyz-CircPath-R' + str(pathR).replace('.','_') + 'West' + '.dat']])
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #=======================================================================
    # END - extract stresses along circumferential paths
    #=======================================================================

    #=======================================================================
    # BEGIN - extract stresses along horizontal paths
    #=======================================================================

    if 'report-stresseshorizontalpaths' in parameters['simulation-pipeline']['analysis'].keys():
        if parameters['simulation-pipeline']['analysis']['report-stresseshorizontalpaths']['start']:
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Extracting stresses along horizontal paths ...',True)
            sessionOdb = session.openOdb(name=odbfullpath)
            session.viewports['Viewport: 1'].setValues(displayedObject=sessionOdb)
            pathYsLow = np.linspace(0,parameters['geometry']['Rf'],parameters['simulation-pipeline']['analysis']['report-stresseshorizontalpaths']['stepParameter'],endpoint=True)
            pathYsUp = np.linspace(parameters['geometry']['Rf'],parameters['geometry']['L'],parameters['simulation-pipeline']['analysis']['report-stresseshorizontalpaths']['stepParameter'],endpoint=True)[1:]
            csvFilename = parameters['output']['local']['directory'].replace('\\','/').split('/')[-1] + '-stresseshorizontalpaths'
            createCSVfile(parameters['output']['local']['directory'],csvFilename,'VARIABLE, y, xi, xf, FOLDER, FILENAME')
            nSegsOnPath = int(parameters['simulation-pipeline']['analysis']['report-stresseshorizontalpaths']['nSegsOnPath'])
            for yNum,pathY in enumerate(pathYsLow):
                xEast = np.sqrt(parameters['geometry']['Rf']*parameters['geometry']['Rf']-pathY*pathY)
                xWest = -xEast
                session.Path(name='HPath-Y' + str(pathY) + 'East', type=POINT_LIST, expression=((xEast,pathY,0.0),(parameters['geometry']['L'],pathY,0.0)))
                session.Path(name='HPath-Y' + str(pathY) + 'West', type=POINT_LIST, expression=((-parameters['geometry']['L'],pathY,0.0),(xWest,pathY,0.0)))
                hpath = session.paths['HPath-Y' + str(pathY) + 'East']
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract stress components...',True)
                # sigmaxx
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_xx',True)
                sigmaxx = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S11' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmaxx-HPath-Y' + str(pathY) + 'East' + '.dat'),xyData=sigmaxx,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S11 [MPa]',str(pathY),str(xEast),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'sigmaxx-HPath-Y' + str(pathY) + 'East' + '.dat']])
                # sigmayy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_yy',True)
                sigmayy = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S22' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmayy-HPath-Y' + str(pathY) + 'East' + '.dat'),xyData=sigmayy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S22 [MPa]',str(pathY),str(xEast),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'sigmayy-HPath-Y' + str(pathY) + 'East' + '.dat']])
                # tauxy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- tau_xy',True)
                tauxy = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S12' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauxy-HPath-Y' + str(pathY) + 'East' + '.dat'),xyData=tauxy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S12 [MPa]',str(pathY),str(xEast),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'tauxy-HPath-Y' + str(pathY) + 'East' + '.dat']])
                # sigmazz
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_zz',True)
                sigmazz = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S33' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmazz-HPath-Y' + str(pathY) + 'East' + '.dat'),xyData=sigmazz,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S33 [MPa]',str(pathY),str(xEast),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'sigmazz-HPath-Y' + str(pathY) + 'East' + '.dat']])
                # tauzx
                #tauzx = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S13' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauzx-HPath-Y' + str(pathY) + 'East' + '.dat'),xyData=tauzx,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S13 [MPa]',str(pathY),str(xEast),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'tauzx-HPath-Y' + str(pathY) + 'East' + '.dat']])
                # tauyz
                #tauyz = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S23' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauyz-HPath-Y' + str(pathY) + 'East' + '.dat'),xyData=tauyz,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S23 [MPa]',str(pathY),str(xEast),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'tauyz-HPath-Y' + str(pathY) + 'East' + '.dat']])
                #
                hpath = session.paths['HPath-Y' + str(pathY) + 'West']
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract stress components...',True)
                # sigmaxx
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_xx',True)
                sigmaxx = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S11' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmaxx-HPath-Y' + str(pathY) + 'West' + '.dat'),xyData=sigmaxx,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S11 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(xWest),parameters['output']['local']['directory'],'sigmaxx-HPath-Y' + str(pathY) + 'West' + '.dat']])
                # sigmayy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_yy',True)
                sigmayy = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S22' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmayy-HPath-Y' + str(pathY) + 'West' + '.dat'),xyData=sigmayy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S22 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(xWest),parameters['output']['local']['directory'],'sigmayy-HPath-Y' + str(pathY) + 'West' + '.dat']])
                # tauxy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- tau_xy',True)
                tauxy = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S12' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauxy-HPath-Y' + str(pathY) + 'West' + '.dat'),xyData=tauxy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S12 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(xWest),parameters['output']['local']['directory'],'tauxy-HPath-Y' + str(pathY) + 'West' + '.dat']])
                # sigmazz
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_zz',True)
                sigmazz = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S33' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmazz-HPath-Y' + str(pathY) + 'West' + '.dat'),xyData=sigmazz,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S33 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(xWest),parameters['output']['local']['directory'],'sigmazz-HPath-Y' + str(pathY) + 'West' + '.dat']])
                # tauzx
                #tauzx = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S13' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauzx-HPath-Y' + str(pathY) + 'West' + '.dat'),xyData=tauzx,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S13 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(xWest),parameters['output']['local']['directory'],'tauzx-HPath-Y' + str(pathY) + 'West' + '.dat']])
                # tauyz
                #tauyz = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S23' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauyz-HPath-Y' + str(pathY) + 'West' + '.dat'),xyData=tauyz,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S23 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(xWest),parameters['output']['local']['directory'],'tauyz-HPath-Y' + str(pathY) + 'West' + '.dat']])
            for yNum,pathY in enumerate(pathYsUp):
                session.Path(name='HPath-Y' + str(pathY), type=POINT_LIST, expression=((-parameters['geometry']['L'],pathY,0.0),(parameters['geometry']['L'],pathY,0.0)))
                hpath = session.paths['HPath-Y' + str(pathY)]
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract stress components...',True)
                # sigmaxx
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_xx',True)
                sigmaxx = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S11' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmaxx-HPath-Y' + str(pathY) + '.dat'),xyData=sigmaxx,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S11 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'sigmaxx-HPath-Y' + str(pathY) + '.dat']])
                # sigmayy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_yy',True)
                sigmayy = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S22' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmayy-HPath-Y' + str(pathY) + '.dat'),xyData=sigmayy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S22 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'sigmayy-HPath-Y' + str(pathY) + '.dat']])
                # tauxy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- tau_xy',True)
                tauxy = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S12' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauxy-HPath-Y' + str(pathY) + '.dat'),xyData=tauxy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S12 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'tauxy-HPath-Y' + str(pathY) + '.dat']])
                # sigmazz
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_zz',True)
                sigmazz = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S33' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmazz-HPath-Y' + str(pathY) + '.dat'),xyData=sigmazz,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S33 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'sigmazz-HPath-Y' + str(pathY) + '.dat']])
                # tauzx
                #tauzx = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S13' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauzx-HPath-Y' + str(pathY) + '.dat'),xyData=tauzx,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S13 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'tauzx-HPath-Y' + str(pathY) + '.dat']])
                # tauyz
                #tauyz = xyPlot.XYDataFromPath(path=hpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S23' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauyz-HPath-Y' + str(pathY) + '.dat'),xyData=tauyz,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S23 [MPa]',str(pathY),str(-parameters['geometry']['L']),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'tauyz-HPath-Y' + str(pathY) + '.dat']])
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #=======================================================================
    # END - extract stresses along horizontal paths
    #=======================================================================

    #=======================================================================
    # BEGIN - extract stresses along vertical paths
    #=======================================================================

    if 'report-stressesverticalpaths' in parameters['simulation-pipeline']['analysis'].keys():
        if parameters['simulation-pipeline']['analysis']['report-stressesverticalpaths']['start']:
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Extracting stresses along vertical paths ...',True)
            sessionOdb = session.openOdb(name=odbfullpath)
            session.viewports['Viewport: 1'].setValues(displayedObject=sessionOdb)
            pathXs = np.linspace(-parameters['geometry']['L'],parameters['geometry']['L'],parameters['simulation-pipeline']['analysis']['report-stressesverticalpaths']['stepParameter'],endpoint=True)
            csvFilename = parameters['output']['local']['directory'].replace('\\','/').split('/')[-1] + '-stressesverticalpaths'
            createCSVfile(parameters['output']['local']['directory'],csvFilename,'VARIABLE, x, yi, yf, FOLDER, FILENAME')
            nSegsOnPath = int(parameters['simulation-pipeline']['analysis']['report-stressesverticalpaths']['nSegsOnPath'])
            for xNum,pathX in enumerate(pathXs):
                if pathX>-parameters['geometry']['Rf'] and pathX<parameters['geometry']['Rf']:
                    startY = np.sqrt(parameters['geometry']['Rf']*parameters['geometry']['Rf']-pathX*pathX)
                else:
                    startY = 0.0
                session.Path(name='VPath-X' + str(pathX), type=POINT_LIST, expression=((pathX,startY,0.0),(pathX,parameters['geometry']['L'],0.0)))
                vpath = session.paths['VPath-X' + str(pathX)]
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract stress components...',True)
                # sigmaxx
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_xx',True)
                sigmaxx = xyPlot.XYDataFromPath(path=vpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S11' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmaxx-VPath-X' + str(pathX) + '.dat'),xyData=sigmaxx,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S11 [MPa]',str(pathX),str(startY),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'sigmaxx-VPath-X' + str(pathX) + '.dat']])
                # sigmayy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_yy',True)
                sigmayy = xyPlot.XYDataFromPath(path=vpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S22' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmayy-VPath-X' + str(pathX) + '.dat'),xyData=sigmayy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S22 [MPa]',str(pathX),str(startY),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'sigmayy-VPath-X' + str(pathX) + '.dat']])
                # tauxy
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- tau_xy',True)
                tauxy = xyPlot.XYDataFromPath(path=vpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S12' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauxy-VPath-X' + str(pathX) + '.dat'),xyData=tauxy,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S12 [MPa]',str(pathX),str(startY),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'tauxy-VPath-X' + str(pathX) + '.dat']])
                # sigmazz
                writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + '-- sigma_zz',True)
                sigmazz = xyPlot.XYDataFromPath(path=vpath,includeIntersections=False,pathStyle=UNIFORM_SPACING,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S33' ), ), ))
                session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'sigmazz-VPath-X' + str(pathX) + '.dat'),xyData=sigmazz,appendMode=OFF)
                appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S33 [MPa]',str(pathX),str(startY),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'sigmazz-VPath-X' + str(pathX) + '.dat']])
                # tauzx
                #tauzx = xyPlot.XYDataFromPath(path=vpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S13' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauzx-VPath-X' + str(pathX) + '.dat'),xyData=tauzx,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S13 [MPa]',str(pathX),str(startY),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'tauzx-VPath-X' + str(pathX) + '.dat']])
                # tauyz
                #tauyz = xyPlot.XYDataFromPath(path=vpath,includeIntersections=False,pathStyle=PATH_POINTS,numIntervals=nSegsOnPath,shape=UNDEFORMED,labelType=NORM_DISTANCE,variable= ('S',INTEGRATION_POINT, ( (COMPONENT, 'S23' ), ), ))
                #session.writeXYReport(fileName=join(parameters['output']['local']['directory'],'tauyz-VPath-X' + str(pathX) + '.dat'),xyData=tauyz,appendMode=OFF)
                #appendCSVfile(parameters['output']['local']['directory'],csvFilename,[['S23 [MPa]',str(pathX),str(startY),str(parameters['geometry']['L']),parameters['output']['local']['directory'],'tauyz-VPath-X' + str(pathX) + '.dat']])
            writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)

    #=======================================================================
    # END - extract stresses along vertical paths
    #=======================================================================

    #=======================================================================
    # BEGIN - extract stresses along the bonded interface
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Extracting stresses along the bonded interface ...',True)

    if parameters['simulation-pipeline']['analysis']['report-stressesatbondedinterface']:
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract node labels of crack faces ...',True)
        crackfaceNodes = []
        crackfaceUndefcoords = getFieldOutput(odb,initialStep,0,'COORD',fiberCrackfaceNodes)
        for value in crackfaceUndefcoords.values:
            if value.nodeLabel not in crackfaceNodes:
                crackfaceNodes.append(value.nodeLabel)
        crackfaceUndefcoords = getFieldOutput(odb,initialStep,0,'COORD',matrixCrackfaceNodes)
        for value in crackfaceUndefcoords.values:
            if value.nodeLabel not in crackfaceNodes:
                crackfaceNodes.append(value.nodeLabel)
        del crackfaceUndefcoords
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract undeformed coordinates along the bonded interface ...',True)
        thirdcircleUndefcoords = getFieldOutput(odb,initialStep,0,'COORD',thirdCircle)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Pair data: x0, y0, R0, theta0, x, y, R, theta, sigma_xx, sigma_zz, sigma_yy, tau_xz, sigma_rr, sigma_tt, tau_rt ...',True)
        thirdcircleStressdata = []
        for value in thirdcircleUndefcoords.values:
            if value.nodeLabel not in crackfaceNodes:
                node = odb.rootAssembly.instances['RVE-ASSEMBLY'].getNodeFromLabel(value.nodeLabel)
                stress = getFieldOutput(odb,-1,-1,'S',node,3)
                defcoords = getFieldOutput(odb,-1,-1,'COORD',node)
                radP0 = np.sqrt(value.data[0]*value.data[0]+value.data[1]*value.data[1])
                angP0 = np.arctan2(value.data[1],value.data[0])
                radP = np.sqrt(defcoords.values[0].data[0]*defcoords.values[0].data[0]+defcoords.values[0].data[1]*defcoords.values[0].data[1])
                angP = np.arctan2(defcoords.values[0].data[1],defcoords.values[0].data[0])
                sigRR,sigTT,tauRT = rotateStress2D(stress.values[0].data[0],stress.values[0].data[1],stress.values[0].data[3],angP0)
                thirdcircleStressdata.append([value.data[0],value.data[1],radP0,angP0*180.0/np.pi,(angP0*180.0/np.pi-parameters['geometry']['deltatheta'])/(180.0-parameters['geometry']['deltatheta']),defcoords.values[0].data[0],defcoords.values[0].data[1],radP,angP*180.0/np.pi,(angP*180.0/np.pi-parameters['geometry']['deltatheta'])/(180.0-parameters['geometry']['deltatheta']),stress.values[0].data[0],stress.values[0].data[1],stress.values[0].data[2],stress.values[0].data[3],sigRR,sigTT,tauRT])
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Save data to csv file ...',True)
        thirdcircleStressdata = np.array(thirdcircleStressdata)
        thirdcircleStressdata = thirdcircleStressdata[np.argsort(thirdcircleStressdata[:,0])]
        createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['stressesatbondedinterface'],'x0 [um], y0 [um], R0 [um], theta0 [deg], (theta0-deltatheta)/(180-deltatheta) [-], x [um], y [um], R [um], theta [deg], (theta-deltatheta)/(180-deltatheta) [-], sigma_xx [MPa], sigma_zz [MPa], sigma_yy [MPa], tau_xz [MPa], sigma_rr [MPa], sigma_tt [MPa], tau_rt [MPa]')
        appendCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['stressesatbondedinterface'],thirdcircleStressdata)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        del thirdcircleStressdata
        del thirdcircleUndefcoords
        del crackfaceNodes
        del thirdCircle
    else:
        createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['stressesatbondedinterface'],'x0 [um], y0 [um], R0 [um], theta0 [deg], (theta0-deltatheta)/(180-deltatheta) [-], x [um], y [um], R [um], theta [deg], (theta-deltatheta)/(180-deltatheta) [-], sigma_xx [MPa], sigma_zz [MPa], sigma_yy [MPa], tau_xz [MPa], sigma_rr [MPa], sigma_tt [MPa], tau_rt [MPa]')

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - extract stresses along the bonded interface
    #=======================================================================

    #=======================================================================
    # BEGIN - compute G0
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Compute G0...',True)
    if parameters['simulation-pipeline']['analysis']['report-stressesatboundary']:
        G0 = np.pi*parameters['geometry']['Rf']*meanSigmaxx*meanSigmaxx*(1+(3.0-4.0*parameters['postproc']['nu-G0']))/(8.0*parameters['postproc']['G-G0'])
    else:
        G0 = 1.0
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - compute G0
    #=======================================================================

    #=======================================================================
    # BEGIN - compute reference frame transformation
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Compute reference frame transformation ...',True)

    undefCracktipCoords = getFieldOutput(odb,initialStep,0,'COORD',fiberCracktip)
    phi = np.arctan2(undefCracktipCoords.values[0].data[1],undefCracktipCoords.values[0].data[0])

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - compute reference frame transformation
    #=======================================================================

    #=======================================================================
    # BEGIN - compute contact zone
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Compute contact zone ...',True)

    if parameters['simulation-pipeline']['analysis']['report-contactzone']:
        if len(parameters['steps'])>1:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '--> THERMAL STEP <--',True)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract displacements on fiber ...',True)
            fiberCrackfaceDisps = getFieldOutput(odb,-2,-1,'U',fiberCrackfaceNodes)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract displacements on matrix ...',True)
            matrixCrackfaceDisps = getFieldOutput(odb,-2,-1,'U',matrixCrackfaceNodes)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            fiberAngles = []
            fiberDisps = []

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Rotate fiber displacements ...',True)
            for value in fiberCrackfaceDisps.values:
                if value.nodeLabel!=undefCracktipCoords.values[0].nodeLabel:
                    node = odb.rootAssembly.instances['RVE-ASSEMBLY'].getNodeFromLabel(value.nodeLabel)
                    undefCoords = getFieldOutput(odb,initialStep,0,'COORD',node)
                    beta = np.arctan2(undefCoords.values[0].data[1],undefCoords.values[0].data[0])
                    fiberAngles.append(beta)
                    fiberDisps.append([np.cos(beta)*value.data[0]+np.sin(beta)*value.data[1],-np.sin(beta)*value.data[0]+np.cos(beta)*value.data[1]])
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            del fiberCrackfaceDisps

            matrixAngles = []
            matrixDisps = []

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Rotate matrix displacements ...',True)
            for v,value in enumerate(matrixCrackfaceDisps.values):
                #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'At node ' + str(v) + ' with label ' + str(value.nodeLabel),True)
                #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Execute odb.rootAssembly.instances[\'RVE-ASSEMBLY\'].getNodeFromLabel(value.nodeLabel)',True)
                node = odb.rootAssembly.instances['RVE-ASSEMBLY'].getNodeFromLabel(value.nodeLabel)
                #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Execute undefCoords = getFieldOutput(odb,-1,0,\'COORD\',node)',True)
                undefCoords = getFieldOutput(odb,initialStep,0,'COORD',node)
                #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Execute beta = np.arctan2(undefCoords.values[0].data[1],undefCoords.values[0].data[0])',True)
                beta = np.arctan2(undefCoords.values[0].data[1],undefCoords.values[0].data[0])
                #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Execute matrixAngles.append(beta)',True)
                matrixAngles.append(beta)
                #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Execute matrixDisps.append([np.cos(beta)*value.data[0]+np.sin(beta)*value.data[1],-np.sin(beta)*value.data[0]+np.cos(beta)*value.data[1]])',True)
                matrixDisps.append([np.cos(beta)*value.data[0]+np.sin(beta)*value.data[1],-np.sin(beta)*value.data[0]+np.cos(beta)*value.data[1]])
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            del matrixCrackfaceDisps

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Sort fiber displacements and angles...',True)
            fiberDisps = np.array(fiberDisps)[np.argsort(fiberAngles)].tolist()
            fiberAngles = np.array(fiberAngles)[np.argsort(fiberAngles)].tolist()
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Sort matrix displacements and angles...',True)
            matrixDisps = np.array(matrixDisps)[np.argsort(matrixAngles)].tolist()
            matrixAngles = np.array(fiberAngles)[np.argsort(matrixAngles)].tolist()
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            crackDisps = []
            uR = []
            uTheta = []

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute crack displacements ...',True)
            for s,dispset in enumerate(fiberDisps):
                crackDisps.append([matrixDisps[s][0]-dispset[0],matrixDisps[s][1]-dispset[1]])
                uR.append(matrixDisps[s][0]-dispset[0])
                uTheta.append(matrixDisps[s][1]-dispset[1])
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute normalized crack displacements ...',True)
            normedcrackDisps = []
            normedbeta = []
            uRmax = np.max(uR)
            uRavg = np.mean(uR)
            uThetamax = np.max(uTheta)
            uThetaavg = np.mean(uTheta)
            uRweightavg = 0.0
            uThetaweightavg = 0.0
            for s, angle in enumerate(fiberAngles[:-1]):
                uRweightavg += (fiberAngles[s+1]-angle)*(uR[s+1]+uR[s])
                uThetaweightavg += (fiberAngles[s+1]-angle)*(uTheta[s+1]+uTheta[s])
            uRweightavg /= 2*phi
            uThetaweightavg /= 2*phi
            for s,dispset in enumerate(crackDisps):
                normedbeta.append(fiberAngles[s]/phi)
                normedcrackDisps.append([dispset[0]/uRmax,dispset[0]/uRavg,dispset[0]/uRweightavg,dispset[1]/uThetamax,dispset[1]/uThetaavg,dispset[1]/uThetaweightavg])
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute contact zone size ...',True)
            phiCZ = 0.0
            phiSZ = phi
            #uRmax = np.max(uR)
            for d,disp in enumerate(uR):
                if disp<0.002*uRmax:
                    phiSZ = fiberAngles[d]
                    phiCZ = phi - fiberAngles[d]
                    break
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Analyze tolerance of contact zone size estimation...',True)
            phiCZtol = []
            phiSZtol = []
            tolCZ = []
            #uRmax = np.max(uR)
            for tol in np.arange(0.0,0.01525,0.00025):
                tolCZ.append(tol)
                phiCZcurrent = 0.0
                phiSZcurrent = phi
                for d,disp in enumerate(uR):
                    if disp<tol*uRmax:
                        phiSZcurrent = fiberAngles[d]
                        phiCZcurrent = phi - fiberAngles[d]
                        break
                phiSZtol.append(phiSZcurrent)
                phiCZtol.append(phiCZcurrent)
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Save to file ...',True)
            createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['thermalcrackdisplacements'],'beta [deg], uR_fiber, uTheta_fiber, uR_matrix, uTheta_matrix, uR, uTheta, beta/deltatheta [-],  uR/max(uR), uR/mean(uR), uR/weightmean(uR), uTheta/max(uTheta), uTheta/mean(uTheta), uR/weightmean(uTheta)')
            for s,dispset in enumerate(crackDisps):
                appendCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['thermalcrackdisplacements'],[[fiberAngles[s]*180.0/np.pi,fiberDisps[s][0],fiberDisps[s][1],matrixDisps[s][0],matrixDisps[s][1],dispset[0],dispset[1],normedbeta[s],normedcrackDisps[s][0],normedcrackDisps[s][1],normedcrackDisps[s][2],normedcrackDisps[s][3],normedcrackDisps[s][4],normedcrackDisps[s][5]]])
            createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['thermalcontactzonetolerance'],'tol [%], phiSZ [deg], phiCZ [deg]')
            for s,tol in enumerate(tolCZ):
                appendCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['thermalcontactzonetolerance'],[[tol,phiSZtol[s]*180.0/np.pi,phiCZtol[s]*180.0/np.pi]])
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            uRthermal = uR
            uThetathermal = uTheta
            phiCZthermal = phiCZ
            phiSZthermal = phiSZ

            del fiberAngles
            del matrixAngles
            del fiberDisps
            del matrixDisps
            del crackDisps
            del normedbeta
            del normedcrackDisps
            del phiSZtol
            del phiCZtol
            del tolCZ
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '--> MECHANICAL STEP <--',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract displacements on fiber ...',True)
        fiberCrackfaceDisps = getFieldOutput(odb,-1,-1,'U',fiberCrackfaceNodes)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract displacements on matrix ...',True)
        matrixCrackfaceDisps = getFieldOutput(odb,-1,-1,'U',matrixCrackfaceNodes)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        fiberAngles = []
        fiberDisps = []

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Rotate fiber displacements ...',True)
        for value in fiberCrackfaceDisps.values:
            if value.nodeLabel!=undefCracktipCoords.values[0].nodeLabel:
                node = odb.rootAssembly.instances['RVE-ASSEMBLY'].getNodeFromLabel(value.nodeLabel)
                undefCoords = getFieldOutput(odb,initialStep,0,'COORD',node)
                beta = np.arctan2(undefCoords.values[0].data[1],undefCoords.values[0].data[0])
                fiberAngles.append(beta)
                fiberDisps.append([np.cos(beta)*value.data[0]+np.sin(beta)*value.data[1],-np.sin(beta)*value.data[0]+np.cos(beta)*value.data[1]])
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        del fiberCrackfaceDisps

        matrixAngles = []
        matrixDisps = []

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Rotate matrix displacements ...',True)
        for v,value in enumerate(matrixCrackfaceDisps.values):
            #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'At node ' + str(v) + ' with label ' + str(value.nodeLabel),True)
            #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Execute odb.rootAssembly.instances[\'RVE-ASSEMBLY\'].getNodeFromLabel(value.nodeLabel)',True)
            node = odb.rootAssembly.instances['RVE-ASSEMBLY'].getNodeFromLabel(value.nodeLabel)
            #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Execute undefCoords = getFieldOutput(odb,-1,0,\'COORD\',node)',True)
            undefCoords = getFieldOutput(odb,initialStep,0,'COORD',node)
            #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Execute beta = np.arctan2(undefCoords.values[0].data[1],undefCoords.values[0].data[0])',True)
            beta = np.arctan2(undefCoords.values[0].data[1],undefCoords.values[0].data[0])
            #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Execute matrixAngles.append(beta)',True)
            matrixAngles.append(beta)
            #writeLineToLogFile(logfilepath,'a',baselogindent + 4*logindent + 'Execute matrixDisps.append([np.cos(beta)*value.data[0]+np.sin(beta)*value.data[1],-np.sin(beta)*value.data[0]+np.cos(beta)*value.data[1]])',True)
            matrixDisps.append([np.cos(beta)*value.data[0]+np.sin(beta)*value.data[1],-np.sin(beta)*value.data[0]+np.cos(beta)*value.data[1]])
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        del matrixCrackfaceDisps

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Sort fiber displacements and angles...',True)
        fiberDisps = np.array(fiberDisps)[np.argsort(fiberAngles)].tolist()
        fiberAngles = np.array(fiberAngles)[np.argsort(fiberAngles)].tolist()
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Sort matrix displacements and angles...',True)
        matrixDisps = np.array(matrixDisps)[np.argsort(matrixAngles)].tolist()
        matrixAngles = np.array(fiberAngles)[np.argsort(matrixAngles)].tolist()
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        crackDisps = []
        uR = []
        uTheta = []

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute crack displacements ...',True)
        for s,dispset in enumerate(fiberDisps):
            crackDisps.append([matrixDisps[s][0]-dispset[0],matrixDisps[s][1]-dispset[1]])
            uR.append(matrixDisps[s][0]-dispset[0])
            uTheta.append(matrixDisps[s][1]-dispset[1])
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute normalized crack displacements ...',True)
        normedcrackDisps = []
        normedbeta = []
        uRmax = np.max(uR)
        uRavg = np.mean(uR)
        uThetamax = np.max(uTheta)
        uThetaavg = np.mean(uTheta)
        uRweightavg = 0.0
        uThetaweightavg = 0.0
        for s, angle in enumerate(fiberAngles[:-1]):
            uRweightavg += (fiberAngles[s+1]-angle)*(uR[s+1]+uR[s])
            uThetaweightavg += (fiberAngles[s+1]-angle)*(uTheta[s+1]+uTheta[s])
        uRweightavg /= 2*phi
        uThetaweightavg /= 2*phi
        for s,dispset in enumerate(crackDisps):
            normedbeta.append(fiberAngles[s]/phi)
            normedcrackDisps.append([dispset[0]/uRmax,dispset[0]/uRavg,dispset[0]/uRweightavg,dispset[1]/uThetamax,dispset[1]/uThetaavg,dispset[1]/uThetaweightavg])
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute contact zone size ...',True)
        phiCZ = 0.0
        phiSZ = phi
        #uRmax = np.max(uR)
        for d,disp in enumerate(uR):
            if disp<0.002*uRmax:
                phiSZ = fiberAngles[d]
                phiCZ = phi - fiberAngles[d]
                break
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Analyze tolerance of contact zone size estimation...',True)
        phiCZtol = []
        phiSZtol = []
        tolCZ = []
        #uRmax = np.max(uR)
        for tol in np.arange(0.0,0.01525,0.00025):
            tolCZ.append(tol)
            phiCZcurrent = 0.0
            phiSZcurrent = phi
            for d,disp in enumerate(uR):
                if disp<tol*uRmax:
                    phiSZcurrent = fiberAngles[d]
                    phiCZcurrent = phi - fiberAngles[d]
                    break
            phiSZtol.append(phiSZcurrent)
            phiCZtol.append(phiCZcurrent)
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Save to file ...',True)
        createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['crackdisplacements'],'beta [deg], uR_fiber, uTheta_fiber, uR_matrix, uTheta_matrix, uR, uTheta, beta/deltatheta [-],  uR/max(uR), uR/mean(uR), uR/weightmean(uR), uTheta/max(uTheta), uTheta/mean(uTheta), uR/weightmean(uTheta)')
        for s,dispset in enumerate(crackDisps):
            appendCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['crackdisplacements'],[[fiberAngles[s]*180.0/np.pi,fiberDisps[s][0],fiberDisps[s][1],matrixDisps[s][0],matrixDisps[s][1],dispset[0],dispset[1],normedbeta[s],normedcrackDisps[s][0],normedcrackDisps[s][1],normedcrackDisps[s][2],normedcrackDisps[s][3],normedcrackDisps[s][4],normedcrackDisps[s][5]]])
        createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['contactzonetolerance'],'tol [%], phiSZ [deg], phiCZ [deg]')
        for s,tol in enumerate(tolCZ):
            appendCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['contactzonetolerance'],[[tol,phiSZtol[s]*180.0/np.pi,phiCZtol[s]*180.0/np.pi]])
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        del fiberAngles
        del matrixAngles
        del fiberDisps
        del matrixDisps
        del crackDisps
        del normedbeta
        del normedcrackDisps
        del phiSZtol
        del phiCZtol
        del tolCZ
    else:
        createCSVfile(parameters['output']['local']['directory'],parameters['output']['local']['filenames']['crackdisplacements'],'beta [deg], uR_fiber, uTheta_fiber, uR_matrix, uTheta_matrix, uR, uTheta, beta/deltatheta [-],  uR/max(uR), uR/mean(uR), uR/weightmean(uR), uTheta/max(uTheta), uTheta/mean(uTheta), uR/weightmean(uTheta)')
        phiCZ = 0.0
        phiSZ = phi
        uR = [0.0]
        uTheta = [0.0]
        phiCZthermal = 0.0
        phiSZthermal = phi
        uRthermal = [0.0]
        uThetathermal = [0.0]

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - compute contact zone
    #=======================================================================

    #=======================================================================
    # BEGIN - compute VCCT
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Compute VCCT ...',True)

    if parameters['simulation-pipeline']['analysis']['report-energyreleaserates']:
        if len(parameters['steps'])>1:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '--> THERMAL STEP <--',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Check if crack faces are pressure-loaded in this step ...',True)
            isPressureLoadedCrack = False
            for load in parameters['loads'].values():
                if ('appliedUniformPressure' in load['type'] or 'applieduniformpressure' in load['type'] or 'applied Uniform Pressure' in load['type'] or 'applied uniform pressure' in load['type']) and 'Temp-Step' in load['stepName'] and ('FiberSurface' in load['set'] or 'MatrixSurface' in load['set']):
                    isPressureLoadedCrack = True
                    uniformP = load['value']
                    writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Pressure loaded crack faces are present, corrected VCCT will be used.',True)
                    break
            if not isPressureLoadedCrack:
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Pressure loaded crack faces are not present.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract forces and displacements ...',True)

            RFcracktip = getFieldOutput(odb,-2,-1,'RF',cracktipDummyNode)
            if 'second' in parameters['mesh']['elements']['order']:
                RFfirstbounded = getFieldOutput(odb,-2,-1,'RF',firstboundedDummyNode)
            fiberCracktipDisplacement = getFieldOutput(odb,-2,-1,'U',fiberCracktipDispMeas)
            matrixCracktipDisplacement = getFieldOutput(odb,-2,-1,'U',matrixCracktipDispMeas)
            if 'second' in parameters['mesh']['elements']['order']:
                fiberFirstboundedDisplacement = getFieldOutput(odb,-2,-1,'U',fiberFirstboundedDispMeas)
                matrixFirstboundedDisplacement = getFieldOutput(odb,-2,-1,'U',matrixFirstboundedDispMeas)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Rotate forces and displacements ...',True)

            xRFcracktip = RFcracktip.values[0].data[0]
            yRFcracktip = RFcracktip.values[0].data[1]
            rRFcracktip = np.cos(phi)*xRFcracktip + np.sin(phi)*yRFcracktip
            thetaRFcracktip = -np.sin(phi)*xRFcracktip + np.cos(phi)*yRFcracktip
            if 'second' in parameters['mesh']['elements']['order']:
                xRFfirstbounded = RFfirstbounded.values[0].data[0]
                yRFfirstbounded = RFfirstbounded.values[0].data[1]
                rRFfirstbounded = np.cos(phi)*xRFfirstbounded + np.sin(phi)*yRFfirstbounded
                thetaRFfirstbounded = -np.sin(phi)*xRFfirstbounded + np.cos(phi)*yRFfirstbounded
                if isPressureLoadedCrack:
                    rRFcracktip -= uniformP*(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0)/6
                    rRFfirstbounded -= 2*uniformP*(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0)/3
            else:
                if isPressureLoadedCrack:
                    rRFcracktip -= uniformP*(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0)/2

            xfiberCracktipDisplacement = fiberCracktipDisplacement.values[0].data[0]
            yfiberCracktipDisplacement = fiberCracktipDisplacement.values[0].data[1]
            rfiberCracktipDisplacement = np.cos(phi)*xfiberCracktipDisplacement + np.sin(phi)*yfiberCracktipDisplacement
            thetafiberCracktipDisplacement = -np.sin(phi)*xfiberCracktipDisplacement + np.cos(phi)*yfiberCracktipDisplacement
            xmatrixCracktipDisplacement = matrixCracktipDisplacement.values[0].data[0]
            ymatrixCracktipDisplacement = matrixCracktipDisplacement.values[0].data[1]
            rmatrixCracktipDisplacement = np.cos(phi)*xmatrixCracktipDisplacement + np.sin(phi)*ymatrixCracktipDisplacement
            thetamatrixCracktipDisplacement = -np.sin(phi)*xmatrixCracktipDisplacement + np.cos(phi)*ymatrixCracktipDisplacement
            if 'second' in parameters['mesh']['elements']['order']:
                xfiberFirstboundedDisplacement = fiberFirstboundedDisplacement.values[0].data[0]
                yfiberFirstboundedDisplacement = fiberFirstboundedDisplacement.values[0].data[1]
                rfiberFirstboundedDisplacement = np.cos(phi)*xfiberFirstboundedDisplacement + np.sin(phi)*yfiberFirstboundedDisplacement
                thetafiberFirstboundedDisplacement = -np.sin(phi)*xfiberFirstboundedDisplacement + np.cos(phi)*yfiberFirstboundedDisplacement
                xmatrixFirstboundedDisplacement = matrixFirstboundedDisplacement.values[0].data[0]
                ymatrixFirstboundedDisplacement = matrixFirstboundedDisplacement.values[0].data[1]
                rmatrixFirstboundedDisplacement = np.cos(phi)*xmatrixFirstboundedDisplacement + np.sin(phi)*ymatrixFirstboundedDisplacement
                thetamatrixFirstboundedDisplacement = -np.sin(phi)*xmatrixFirstboundedDisplacement + np.cos(phi)*ymatrixFirstboundedDisplacement

            xcracktipDisplacement = xmatrixCracktipDisplacement - xfiberCracktipDisplacement
            ycracktipDisplacement = ymatrixCracktipDisplacement - yfiberCracktipDisplacement
            rcracktipDisplacement = rmatrixCracktipDisplacement - rfiberCracktipDisplacement
            thetacracktipDisplacement = thetamatrixCracktipDisplacement - thetafiberCracktipDisplacement
            if 'second' in parameters['mesh']['elements']['order']:
                xfirstboundedDisplacement = xmatrixFirstboundedDisplacement - xfiberFirstboundedDisplacement
                yfirstboundedDisplacement = ymatrixFirstboundedDisplacement - yfiberFirstboundedDisplacement
                rfirstboundedDisplacement = rmatrixFirstboundedDisplacement - rfiberFirstboundedDisplacement
                thetafirstboundedDisplacement = thetamatrixFirstboundedDisplacement - thetafiberFirstboundedDisplacement

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute VCCT with GTOT=GI+GII ...',True)

            if 'second' in parameters['mesh']['elements']['order']:
                GI = np.abs(0.5*(rRFcracktip*rcracktipDisplacement+rRFfirstbounded*rfirstboundedDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
                GII = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement+thetaRFfirstbounded*thetafirstboundedDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
                GTOTequiv = np.abs(0.5*(xRFcracktip*xcracktipDisplacement+yRFcracktip*ycracktipDisplacement+xRFfirstbounded*xfirstboundedDisplacement+yRFfirstbounded*yfirstboundedDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
            else:
                GI = np.abs(0.5*(rRFcracktip*rcracktipDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
                GII = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
                GTOTequiv = np.abs(0.5*(xRFcracktip*xcracktipDisplacement+yRFcracktip*ycracktipDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))

            GTOT = GI + GII

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute VCCT with GI=GTOT-GII ...',True)

            if 'second' in parameters['mesh']['elements']['order']:
                GIIv2 = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement+thetaRFfirstbounded*thetafirstboundedDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
            else:
                GIIv2 = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))

            GTOTv2 = thermalJintegrals[-1]

            GIv2 = GTOTv2 - GIIv2

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Save to file ...',True)
            if 'second' in parameters['mesh']['elements']['order']:
                appendCSVfile(parameters['output']['global']['directory'],parameters['output']['global']['filenames']['thermalenergyreleaserate'],[[parameters['geometry']['deltatheta'],parameters['geometry']['Rf'],parameters['geometry']['L'],parameters['geometry']['L']/parameters['geometry']['Rf'],phiCZthermal*180.0/np.pi,G0,GI/G0,GII/G0,GTOT/G0,GIv2/G0,GIIv2/G0,GTOTv2/G0,GTOTequiv/G0,GI,GII,GTOT,GIv2,GIIv2,GTOTv2,GTOTequiv,np.min(uRthermal),np.max(uRthermal),np.mean(uRthermal),np.min(uThetathermal),np.max(uThetathermal),np.mean(uThetathermal),phiSZthermal*180.0/np.pi,xRFcracktip,yRFcracktip,xRFfirstbounded,yRFfirstbounded,rRFcracktip,thetaRFcracktip,rRFfirstbounded,thetaRFfirstbounded,xcracktipDisplacement,ycracktipDisplacement,rcracktipDisplacement,thetacracktipDisplacement,xfirstboundedDisplacement,yfirstboundedDisplacement,rfirstboundedDisplacement,thetafirstboundedDisplacement,xfiberCracktipDisplacement,yfiberCracktipDisplacement,rfiberCracktipDisplacement,thetafiberCracktipDisplacement,xfiberFirstboundedDisplacement,yfiberFirstboundedDisplacement,rfiberFirstboundedDisplacement,thetafiberFirstboundedDisplacement,xmatrixCracktipDisplacement,ymatrixCracktipDisplacement,rmatrixCracktipDisplacement,thetamatrixCracktipDisplacement,xmatrixFirstboundedDisplacement,ymatrixFirstboundedDisplacement,rmatrixFirstboundedDisplacement,thetamatrixFirstboundedDisplacement]])
            else:
                appendCSVfile(parameters['output']['global']['directory'],parameters['output']['global']['filenames']['thermalenergyreleaserate'],[[parameters['geometry']['deltatheta'],parameters['geometry']['Rf'],parameters['geometry']['L'],parameters['geometry']['L']/parameters['geometry']['Rf'],phiCZthermal*180.0/np.pi,G0,GI/G0,GII/G0,GTOT/G0,GIv2/G0,GIIv2/G0,GTOTv2/G0,GTOTequiv/G0,GI,GII,GTOT,GIv2,GIIv2,GTOTv2,GTOTequiv,np.min(uRthermal),np.max(uRthermal),np.mean(uRthermal),np.min(uThetathermal),np.max(uThetathermal),np.mean(uThetathermal),phiSZthermal*180.0/np.pi,xRFcracktip,yRFcracktip,rRFcracktip,thetaRFcracktip,xcracktipDisplacement,ycracktipDisplacement,rcracktipDisplacement,thetacracktipDisplacement,xfiberCracktipDisplacement,yfiberCracktipDisplacement,rfiberCracktipDisplacement,thetafiberCracktipDisplacement,xmatrixCracktipDisplacement,ymatrixCracktipDisplacement,rmatrixCracktipDisplacement,thetamatrixCracktipDisplacement]])
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '--> MECHANICAL STEP <--',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Check if crack faces are pressure-loaded in this step ...',True)
        isPressureLoadedCrack = False
        for load in parameters['loads'].values():
            if ('appliedUniformPressure' in load['type'] or 'applieduniformpressure' in load['type'] or 'applied Uniform Pressure' in load['type'] or 'applied uniform pressure' in load['type']) and 'Load-Step' in load['stepName'] and ('FiberSurface' in load['set'] or 'MatrixSurface' in load['set']):
                isPressureLoadedCrack = True
                uniformP = load['value']
                writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Pressure loaded crack faces are present, corrected VCCT will be used.',True)
                break
        if not isPressureLoadedCrack:
            writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Pressure loaded crack faces are not present.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Extract forces and displacements ...',True)

        RFcracktip = getFieldOutput(odb,-1,-1,'RF',cracktipDummyNode)
        if 'second' in parameters['mesh']['elements']['order']:
            RFfirstbounded = getFieldOutput(odb,-1,-1,'RF',firstboundedDummyNode)
        fiberCracktipDisplacement = getFieldOutput(odb,-1,-1,'U',fiberCracktipDispMeas)
        matrixCracktipDisplacement = getFieldOutput(odb,-1,-1,'U',matrixCracktipDispMeas)
        if 'second' in parameters['mesh']['elements']['order']:
            fiberFirstboundedDisplacement = getFieldOutput(odb,-1,-1,'U',fiberFirstboundedDispMeas)
            matrixFirstboundedDisplacement = getFieldOutput(odb,-1,-1,'U',matrixFirstboundedDispMeas)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Rotate forces and displacements ...',True)

        xRFcracktip = RFcracktip.values[0].data[0]
        yRFcracktip = RFcracktip.values[0].data[1]
        rRFcracktip = np.cos(phi)*xRFcracktip + np.sin(phi)*yRFcracktip
        thetaRFcracktip = -np.sin(phi)*xRFcracktip + np.cos(phi)*yRFcracktip
        if 'second' in parameters['mesh']['elements']['order']:
            xRFfirstbounded = RFfirstbounded.values[0].data[0]
            yRFfirstbounded = RFfirstbounded.values[0].data[1]
            rRFfirstbounded = np.cos(phi)*xRFfirstbounded + np.sin(phi)*yRFfirstbounded
            thetaRFfirstbounded = -np.sin(phi)*xRFfirstbounded + np.cos(phi)*yRFfirstbounded
            if isPressureLoadedCrack:
                rRFcracktip -= uniformP*(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0)/6
                rRFfirstbounded -= 2*uniformP*(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0)/3
        else:
            if isPressureLoadedCrack:
                rRFcracktip -= uniformP*(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0)/2


        xfiberCracktipDisplacement = fiberCracktipDisplacement.values[0].data[0]
        yfiberCracktipDisplacement = fiberCracktipDisplacement.values[0].data[1]
        rfiberCracktipDisplacement = np.cos(phi)*xfiberCracktipDisplacement + np.sin(phi)*yfiberCracktipDisplacement
        thetafiberCracktipDisplacement = -np.sin(phi)*xfiberCracktipDisplacement + np.cos(phi)*yfiberCracktipDisplacement
        xmatrixCracktipDisplacement = matrixCracktipDisplacement.values[0].data[0]
        ymatrixCracktipDisplacement = matrixCracktipDisplacement.values[0].data[1]
        rmatrixCracktipDisplacement = np.cos(phi)*xmatrixCracktipDisplacement + np.sin(phi)*ymatrixCracktipDisplacement
        thetamatrixCracktipDisplacement = -np.sin(phi)*xmatrixCracktipDisplacement + np.cos(phi)*ymatrixCracktipDisplacement
        if 'second' in parameters['mesh']['elements']['order']:
            xfiberFirstboundedDisplacement = fiberFirstboundedDisplacement.values[0].data[0]
            yfiberFirstboundedDisplacement = fiberFirstboundedDisplacement.values[0].data[1]
            rfiberFirstboundedDisplacement = np.cos(phi)*xfiberFirstboundedDisplacement + np.sin(phi)*yfiberFirstboundedDisplacement
            thetafiberFirstboundedDisplacement = -np.sin(phi)*xfiberFirstboundedDisplacement + np.cos(phi)*yfiberFirstboundedDisplacement
            xmatrixFirstboundedDisplacement = matrixFirstboundedDisplacement.values[0].data[0]
            ymatrixFirstboundedDisplacement = matrixFirstboundedDisplacement.values[0].data[1]
            rmatrixFirstboundedDisplacement = np.cos(phi)*xmatrixFirstboundedDisplacement + np.sin(phi)*ymatrixFirstboundedDisplacement
            thetamatrixFirstboundedDisplacement = -np.sin(phi)*xmatrixFirstboundedDisplacement + np.cos(phi)*ymatrixFirstboundedDisplacement

        xcracktipDisplacement = xmatrixCracktipDisplacement - xfiberCracktipDisplacement
        ycracktipDisplacement = ymatrixCracktipDisplacement - yfiberCracktipDisplacement
        rcracktipDisplacement = rmatrixCracktipDisplacement - rfiberCracktipDisplacement
        thetacracktipDisplacement = thetamatrixCracktipDisplacement - thetafiberCracktipDisplacement
        if 'second' in parameters['mesh']['elements']['order']:
            xfirstboundedDisplacement = xmatrixFirstboundedDisplacement - xfiberFirstboundedDisplacement
            yfirstboundedDisplacement = ymatrixFirstboundedDisplacement - yfiberFirstboundedDisplacement
            rfirstboundedDisplacement = rmatrixFirstboundedDisplacement - rfiberFirstboundedDisplacement
            thetafirstboundedDisplacement = thetamatrixFirstboundedDisplacement - thetafiberFirstboundedDisplacement

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute VCCT with GTOT=GI+GII ...',True)

        if 'second' in parameters['mesh']['elements']['order']:
            GI = np.abs(0.5*(rRFcracktip*rcracktipDisplacement+rRFfirstbounded*rfirstboundedDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
            GII = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement+thetaRFfirstbounded*thetafirstboundedDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
            GTOTequiv = np.abs(0.5*(xRFcracktip*xcracktipDisplacement+yRFcracktip*ycracktipDisplacement+xRFfirstbounded*xfirstboundedDisplacement+yRFfirstbounded*yfirstboundedDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
        else:
            GI = np.abs(0.5*(rRFcracktip*rcracktipDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
            GII = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
            GTOTequiv = np.abs(0.5*(xRFcracktip*xcracktipDisplacement+yRFcracktip*ycracktipDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))

        GTOT = GI + GII

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Compute VCCT with GI=GTOT-GII ...',True)

        if 'second' in parameters['mesh']['elements']['order']:
            GIIv2 = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement+thetaRFfirstbounded*thetafirstboundedDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))
        else:
            GIIv2 = np.abs(0.5*(thetaRFcracktip*thetacracktipDisplacement)/(parameters['geometry']['Rf']*parameters['mesh']['size']['delta']*np.pi/180.0))

        GTOTv2 = Jintegrals[-1]

        GIv2 = GTOTv2 - GIIv2

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + 'Save to file ...',True)
        if 'second' in parameters['mesh']['elements']['order']:
            appendCSVfile(parameters['output']['global']['directory'],parameters['output']['global']['filenames']['energyreleaserate'],[[parameters['geometry']['deltatheta'],parameters['geometry']['Rf'],parameters['geometry']['L'],parameters['geometry']['L']/parameters['geometry']['Rf'],phiCZ*180.0/np.pi,G0,GI/G0,GII/G0,GTOT/G0,GIv2/G0,GIIv2/G0,GTOTv2/G0,GTOTequiv/G0,GI,GII,GTOT,GIv2,GIIv2,GTOTv2,GTOTequiv,np.min(uR),np.max(uR),np.mean(uR),np.min(uTheta),np.max(uTheta),np.mean(uTheta),phiSZ*180.0/np.pi,xRFcracktip,yRFcracktip,xRFfirstbounded,yRFfirstbounded,rRFcracktip,thetaRFcracktip,rRFfirstbounded,thetaRFfirstbounded,xcracktipDisplacement,ycracktipDisplacement,rcracktipDisplacement,thetacracktipDisplacement,xfirstboundedDisplacement,yfirstboundedDisplacement,rfirstboundedDisplacement,thetafirstboundedDisplacement,xfiberCracktipDisplacement,yfiberCracktipDisplacement,rfiberCracktipDisplacement,thetafiberCracktipDisplacement,xfiberFirstboundedDisplacement,yfiberFirstboundedDisplacement,rfiberFirstboundedDisplacement,thetafiberFirstboundedDisplacement,xmatrixCracktipDisplacement,ymatrixCracktipDisplacement,rmatrixCracktipDisplacement,thetamatrixCracktipDisplacement,xmatrixFirstboundedDisplacement,ymatrixFirstboundedDisplacement,rmatrixFirstboundedDisplacement,thetamatrixFirstboundedDisplacement]])
        else:
            appendCSVfile(parameters['output']['global']['directory'],parameters['output']['global']['filenames']['energyreleaserate'],[[parameters['geometry']['deltatheta'],parameters['geometry']['Rf'],parameters['geometry']['L'],parameters['geometry']['L']/parameters['geometry']['Rf'],phiCZ*180.0/np.pi,G0,GI/G0,GII/G0,GTOT/G0,GIv2/G0,GIIv2/G0,GTOTv2/G0,GTOTequiv/G0,GI,GII,GTOT,GIv2,GIIv2,GTOTv2,GTOTequiv,np.min(uR),np.max(uR),np.mean(uR),np.min(uTheta),np.max(uTheta),np.mean(uTheta),phiSZ*180.0/np.pi,xRFcracktip,yRFcracktip,rRFcracktip,thetaRFcracktip,xcracktipDisplacement,ycracktipDisplacement,rcracktipDisplacement,thetacracktipDisplacement,xfiberCracktipDisplacement,yfiberCracktipDisplacement,rfiberCracktipDisplacement,thetafiberCracktipDisplacement,xmatrixCracktipDisplacement,ymatrixCracktipDisplacement,rmatrixCracktipDisplacement,thetamatrixCracktipDisplacement]])
        writeLineToLogFile(logfilepath,'a',baselogindent + 3*logindent + '... done.',True)

    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - compute VCCT
    #=======================================================================

    #=======================================================================
    # BEGIN - close ODB
    #=======================================================================
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + 'Closing ODB database ...',True)
    odb.close()
    writeLineToLogFile(logfilepath,'a',baselogindent + 2*logindent + '... done.',True)
    #=======================================================================
    # END - close ODB
    #=======================================================================

    writeLineToLogFile(logfilepath,'a',baselogindent + logindent + 'Exiting function: analyzeRVEresults(wd,odbname,parameters)',True)



def main(argv):

    #=======================================================================
    # BEGIN - PARSE COMMAND LINE
    #=======================================================================

    debug = False

    for a,arg in enumerate(argv):
        if '-help' in arg:
            printHelp()
        elif '-dir' in arg or '-directory' in arg:
            inputDirectory = argv[a+1]
        elif '-data' in arg:
            dataFile = argv[a+1]
        elif '-iterables' in arg:
            iterablesFile = argv[a+1]
        elif '-plot' in arg:
            plotFile = argv[a+1]
        elif '-debug' in arg:
            debug = True
            print >> sys.__stdout__,(' ')
            print >> sys.__stdout__,(' ')
            print >> sys.__stdout__,('>>>>-----------------------<<<<')
            print >> sys.__stdout__,('>>>> Running in DEBUG MODE <<<<')
            print >> sys.__stdout__,('>>>>-----------------------<<<<')
            print >> sys.__stdout__,(' ')
            print >> sys.__stdout__,(' ')

    if 'inputDirectory' not in locals():
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,('!!! ERROR: missing input directory !!!')
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,(' ')
        printHelp()
    if 'dataFile' not in locals():
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,('!!! ERROR: missing data file !!!')
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,(' ')
        printHelp()
    if 'iterablesFile' not in locals():
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,('!!! ERROR: missing iterables file !!!')
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,(' ')
        printHelp()
    if 'plotFile' not in locals():
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,('!!! ERROR: missing plot file !!!')
        print >> sys.__stdout__,(' ')
        print >> sys.__stdout__,(' ')
        printHelp()

    #=======================================================================
    # END - PARSE COMMAND LINE
    #=======================================================================

    #=======================================================================
    # BEGIN - DATA
    #=======================================================================

    # units are already the ones used in simulation, not SI

    ABQbuiltinDict = {'ISOTROPIC':ISOTROPIC,
                      'ENGINEERING_CONSTANTS':ENGINEERING_CONSTANTS,
                      'MIDDLE_SURFACE':MIDDLE_SURFACE,
                      'FROM_SECTION':FROM_SECTION}

    if inputDirectory[-1]=='/' or inputDirectory[-1]=='\\':
        inputDirectory = inputDirectory[:-1]

    with open(join(inputDirectory,dataFile.split('.')[0]+'.deck'),'r') as deck:
        decklines = deck.readlines()

    keywords = []
    values = []

    for line in decklines:
        if line[0] == '#':
            continue
        removeComment = line.replace('\n','').split('#')[0]
        keywordSet = removeComment.split('@')[0]
        keywords.append(keywordSet.replace(' ','').split(','))
        dataType = removeComment.split('$')[1]
        if  'list of boolean' in dataType:
            listAsString = removeComment.split('@')[1].split('$')[0].replace(' ','').replace('[','').replace(']','').split(',')
            dataList = []
            for dataString in listAsString:
                dataList.append(ast.literal_eval(dataString))
            values.append(dataList)
        elif  'list of int' in dataType:
            listAsString = removeComment.split('@')[1].split('$')[0].replace(' ','').replace('[','').replace(']','').split(',')
            dataList = []
            for dataString in listAsString:
                dataList.append(int(dataString))
            values.append(dataList)
        elif  'list of float' in dataType:
            listAsString = removeComment.split('@')[1].split('$')[0].replace(' ','').replace('[','').replace(']','').split(',')
            dataList = []
            for dataString in listAsString:
                dataList.append(float(dataString))
            values.append(dataList)
        elif  'list of string' in dataType:
            listAsString = removeComment.split('@')[1].split('$')[0].replace(' ','').replace('[','').replace(']','').split(',')
            dataList = []
            for dataString in listAsString:
                dataList.append(str(dataString))
            values.append(dataList)
        elif  'list of ABAQUS keyword' in dataType:
            values.append(ABQbuiltinDict[removeComment.split('@')[1].split('$')[0]])
            listAsString = removeComment.split('@')[1].split('$')[0].replace(' ','').replace('[','').replace(']','').split(',')
            dataList = []
            for dataString in listAsString:
                dataList.append(ABQbuiltinDict[dataString])
            values.append(dataList)
        elif 'boolean' in dataType:
            values.append(ast.literal_eval(removeComment.split('@')[1].split('$')[0].replace(' ','')))
        elif  'int' in dataType:
            values.append(int(removeComment.split('@')[1].split('$')[0].replace(' ','')))
        elif  'float' in dataType:
            values.append(float(removeComment.split('@')[1].split('$')[0].replace(' ','')))
        elif  'string' in dataType:
            values.append(str(removeComment.split('@')[1].split('$')[0].replace(' ','')))
        elif  'ABAQUS keyword' in dataType:
            values.append(ABQbuiltinDict[removeComment.split('@')[1].split('$')[0].replace(' ','')])

    RVEparams = {}

    for k,keywordSet in enumerate(keywords):
        fillDataDictionary(RVEparams,keywordSet,values[k])

    # parameters for iterations
    # RVEparams['modelname']
    # RVEparams['deltatheta']
    # RVEparams['deltapsi']
    # RVEparams['deltaphi']

    #=======================================================================
    # END - DATA
    #=======================================================================

    #=======================================================================
    # BEGIN - ITERABLES
    #=======================================================================

    with open(join(inputDirectory,iterablesFile.split('.')[0]+'.deck'),'r') as deck:
        decklines = deck.readlines()

    for l,line in enumerate(decklines):
        if line[0] == '#':
            continue
        elif 'basename' in line:
            basename = str(line.replace('\n','').split('#')[0].split('$')[0].split('@')[1].replace(' ',''))
        elif 'free parameters' in line:
            freeParamsStart = l+1

    keywords = []
    values = []
    lenOfValues = []

    for line in decklines[freeParamsStart:]:
        if line[0] == '#':
            continue
        removeComment = line.replace('\n','').split('#')[0]
        keywordSet = removeComment.split('@')[0]
        keywords.append(keywordSet.replace(' ','').split(','))
        dataType = removeComment.split('$')[1]
        listAsString = removeComment.split('@')[1].split('$')[0].replace('[','').replace(']','').split(',')
        dataList = []
        for dataString in listAsString:
            dataList.append(float(dataString))
        if 'min' in dataType and 'max' in dataType and 'step' in dataType:
            values.append(np.arange(dataList[0],dataList[1]+dataList[2],dataList[2]))
        else:
            values.append(dataList)
        lenOfValues.append(len(values[-1]))

    lenSortedIndeces = np.argsort(lenOfValues)
    sortedValues = []
    sortedKeywords = []
    for index in lenSortedIndeces:
        sortedValues.append(values[index])
        sortedKeywords.append(keywords[index])

    iterationsSets = []
    indecesCollection = []

    totalSets = 1
    for valueSet in sortedValues:
        totalSets *= len(valueSet)

    indeces = []
    for j in range(0,len(sortedKeywords)):
        indeces.append(0)
    indecesCollection.append(indeces)
    iterationSet = []
    for i,index in enumerate(indeces):
        iterationSet.append(sortedValues[i][index])
    iterationsSets.append(iterationSet)

    for k in range(1,totalSets):
        indeces = []
        for j in range(0,len(sortedKeywords)-1):
            indeces.append(0)
        if indecesCollection[k-1][-1]==len(sortedValues[-1])-1:
            indeces.append(0)
        else:
            indeces.append(indecesCollection[k-1][-1] + 1)
        for j in range(len(sortedKeywords)-2,-1,-1):
            if indeces[j+1]==0:
                if indecesCollection[k-1][j]==len(sortedValues[j])-1:
                    indeces.append(0)
                else:
                    indeces.append(indecesCollection[k-1][j] + 1)
            else:
                indeces.append(indecesCollection[k-1][j])
        indecesCollection.append(indeces)
        iterationSet = []
        for i,index in enumerate(indeces):
            iterationSet.append(sortedValues[i][index])
        iterationsSets.append(iterationSet)

    #=======================================================================
    # END - ITERABLES
    #=======================================================================

    #=======================================================================
    # BEGIN - PLOT SETTINGS
    #=======================================================================

    with open(join(inputDirectory,plotFile.split('.')[0]+'.deck'),'r') as deck:
        decklines = deck.readlines()

    keywords = []
    values = []

    for line in decklines:
        if line[0] == '#':
            continue
        removeComment = line.replace('\n','').split('#')[0]
        keywordSet = removeComment.split('@')[0]
        keywords.append(keywordSet.replace(' ','').split(','))
        dataType = removeComment.split('$')[1]
        if  'list of boolean' in dataType:
            listAsString = removeComment.split('@')[1].split('$')[0].replace(' ','').replace('[','').replace(']','').split(',')
            dataList = []
            for dataString in listAsString:
                dataList.append(ast.literal_eval(dataString))
            values.append(dataList)
        elif  'list of int' in dataType:
            listAsString = removeComment.split('@')[1].split('$')[0].replace(' ','').replace('[','').replace(']','').split(',')
            dataList = []
            for dataString in listAsString:
                dataList.append(int(dataString))
            values.append(dataList)
        elif  'list of float' in dataType:
            listAsString = removeComment.split('@')[1].split('$')[0].replace(' ','').replace('[','').replace(']','').split(',')
            dataList = []
            for dataString in listAsString:
                dataList.append(float(dataString))
            values.append(dataList)
        elif  'list of string' in dataType:
            listAsString = removeComment.split('@')[1].split('$')[0].replace('[','').replace(']','').split(',')
            dataList = []
            for dataString in listAsString:
                dataList.append(str(dataString))
            values.append(dataList)
        elif  'list of ABAQUS keyword' in dataType:
            values.append(ABQbuiltinDict[removeComment.split('@')[1].split('$')[0]])
            listAsString = removeComment.split('@')[1].split('$')[0].replace(' ','').replace('[','').replace(']','').split(',')
            dataList = []
            for dataString in listAsString:
                dataList.append(ABQbuiltinDict[dataString])
            values.append(dataList)
        elif 'boolean' in dataType:
            values.append(ast.literal_eval(removeComment.split('@')[1].split('$')[0].replace(' ','')))
        elif  'int' in dataType:
            values.append(int(removeComment.split('@')[1].split('$')[0].replace(' ','')))
        elif  'float' in dataType:
            values.append(float(removeComment.split('@')[1].split('$')[0].replace(' ','')))
        elif  'string' in dataType:
            values.append(str(removeComment.split('@')[1].split('$')[0]))
        elif  'ABAQUS keyword' in dataType:
            values.append(ABQbuiltinDict[removeComment.split('@')[1].split('$')[0].replace(' ','')])

    for k,keywordSet in enumerate(keywords):
        fillDataDictionary(RVEparams,keywordSet,values[k])

    #=======================================================================
    # END - PLOT SETTINGS
    #=======================================================================

    #=======================================================================
    # BEGIN - ANALYSIS
    #=======================================================================

    workDir = RVEparams['input']['wd']
    RVEparams['output']['global']['filenames']['inputdata'] = basename + '_InputData'
    RVEparams['output']['global']['filenames']['performances'] = basename + '_ABQ-Performances'
    RVEparams['output']['global']['filenames']['energyreleaserate'] = basename + '_ERRTS'
    if len(RVEparams['steps'])>1:
        RVEparams['output']['global']['filenames']['thermalenergyreleaserate'] = basename + '_thermalERRTS'

    logfilename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '_ABQ-RVE-generation-and-analysis' + '.log'
    logfilefullpath = join(workDir,logfilename)
    logindent = '    '

    if not os.path.exists(RVEparams['output']['global']['directory']):
            os.mkdir(RVEparams['output']['global']['directory'])

    with open(logfilefullpath,'w') as log:
        log.write('Automatic generation and FEM analysis of RVEs with Abaqus Python' + '\n')

    createCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_TIME','ITERATION PARAMETER VALUE, T(createRVE()) [s], T(modifyRVEinputfile()) [s], T(runRVEsimulation()) [s], T(analyzeRVEresults()) [s],TOTAL TIME FOR ITERATION [s]')

    createCSVfile(RVEparams['output']['global']['directory'],RVEparams['output']['global']['filenames']['inputdata'],'Rf [um],L [um],L/Rf [-],Vff [-],BC,applied strain [-],fiber,matrix')
    appendCSVfile(RVEparams['output']['global']['directory'],RVEparams['output']['global']['filenames']['inputdata'],[[RVEparams['geometry']['Rf'],RVEparams['geometry']['L'],RVEparams['geometry']['L']/RVEparams['geometry']['Rf'],(RVEparams['geometry']['Rf']*RVEparams['geometry']['Rf']*np.pi)/(4*RVEparams['geometry']['L']*RVEparams['geometry']['L']),RVEparams['sections']['1']['material'],RVEparams['sections']['2']['material']]])

    createCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist','ABSOLUTE PATH, NAME, TO PLOT, PLOT VARIABLES')
    appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['global']['directory'],RVEparams['output']['global']['filenames']['inputdata']+'.csv'),'MODEL-DATA',RVEparams['plot']['global']['inputdata']['toPlot'],RVEparams['plot']['global']['inputdata']['variables']]])
    appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['global']['directory'],RVEparams['output']['global']['filenames']['energyreleaserate']+'.csv'),'GLOBAL-ERRTS',RVEparams['plot']['global']['errts']['toPlot'],RVEparams['plot']['global']['errts']['variables']]])
    if len(RVEparams['steps'])>1:
        appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['global']['directory'],RVEparams['output']['global']['filenames']['thermalenergyreleaserate']+'.csv'),'GLOBAL-THERMALERRTS',RVEparams['plot']['global']['errts']['toPlot'],RVEparams['plot']['global']['errts']['variables']]])
    appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['global']['directory'],logfilename.split('.')[0] + '_TIME'+'.csv'),'GLOBAL-TIME',RVEparams['plot']['global']['globaltime']['toPlot'],RVEparams['plot']['global']['globaltime']['variables']]])
    appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['global']['directory'],RVEparams['output']['global']['filenames']['performances']+'.csv'),'GLOBAL-ABQperformances',RVEparams['plot']['global']['abqperf']['toPlot'],RVEparams['plot']['global']['abqperf']['variables']]])

    createCSVfile(RVEparams['output']['global']['directory'],RVEparams['output']['global']['filenames']['performances'],'PROJECT NAME, NUMBER OF CPUS [-], USER TIME [s], SYSTEM TIME [s], USER TIME/TOTAL CPU TIME [%], SYSTEM TIME/TOTAL CPU TIME [%], TOTAL CPU TIME [s], WALLCLOCK TIME [s], WALLCLOCK TIME [m], WALLCLOCK TIME [h], WALLCLOCK TIME/TOTAL CPU TIME [%], ESTIMATED FLOATING POINT OPERATIONS PER ITERATION [-], MINIMUM REQUIRED MEMORY [MB], MEMORY TO MINIMIZE I/O [MB], TOTAL NUMBER OF ELEMENTS [-], NUMBER OF ELEMENTS DEFINED BY THE USER [-], NUMBER OF ELEMENTS DEFINED BY THE PROGRAM [-], TOTAL NUMBER OF NODES [-], NUMBER OF NODES DEFINED BY THE USER [-], NUMBER OF NODES DEFINED BY THE PROGRAM [-], TOTAL NUMBER OF VARIABLES [-]')

    titleline = ''
    if 'second' in RVEparams['mesh']['elements']['order']:
        titleline = 'deltatheta [deg],Rf,L,L/Rf,phiCZ [deg],G0,GI/G0,GII/G0,GTOT/G0,GIv2/G0,GIIv2/G0,GTOTv2/G0,GTOTequiv/G0,GI,GII,GTOT,GIv2,GIIv2,GTOTv2,GTOTequiv,np.min(uR),np.max(uR),np.mean(uR),np.min(uTheta),np.max(uTheta),np.mean(uTheta),phiSZ [deg],xRFcracktip,yRFcracktip,xRFfirstbounded,yRFfirstbounded,rRFcracktip,thetaRFcracktip,rRFfirstbounded,thetaRFfirstbounded,xcracktipDisplacement,ycracktipDisplacement,rcracktipDisplacement,thetacracktipDisplacement,xfirstboundedDisplacement,yfirstboundedDisplacement,rfirstboundedDisplacement,thetafirstboundedDisplacement,xfiberCracktipDisplacement,yfiberCracktipDisplacement,rfiberCracktipDisplacement,thetafiberCracktipDisplacement,xfiberFirstboundedDisplacement,yfiberFirstboundedDisplacement,rfiberFirstboundedDisplacement,thetafiberFirstboundedDisplacement,xmatrixracktipDisplacement,ymatrixCracktipDisplacement,rmatrixCracktipDisplacement,thetamatrixCracktipDisplacement,xmatrixFirstboundedDisplacement,ymatrixFirstboundedDisplacement,rmatrixFirstboundedDisplacement,thetamatrixFirstboundedDisplacement'
    else:
        titleline = 'deltatheta [deg],Rf,L,L/Rf,phiCZ [deg],G0,GI/G0,GII/G0,GTOT/G0,GIv2/G0,GIIv2/G0,GTOTv2/G0,GTOTequiv/G0,GI,GII,GTOT,GIv2,GIIv2,GTOTv2,GTOTequiv,np.min(uR),np.max(uR),np.mean(uR),np.min(uTheta),np.max(uTheta),np.mean(uTheta),phiSZ [deg],xRFcracktip,yRFcracktip,rRFcracktip,thetaRFcracktip,xcracktipDisplacement,ycracktipDisplacement,rcracktipDisplacement,thetacracktipDisplacement,xfiberCracktipDisplacement,yfiberCracktipDisplacement,rfiberCracktipDisplacement,thetafiberCracktipDisplacement,xmatrixCracktipDisplacement,ymatrixCracktipDisplacement,rmatrixCracktipDisplacement,thetamatrixCracktipDisplacement'
    createCSVfile(RVEparams['output']['global']['directory'],RVEparams['output']['global']['filenames']['energyreleaserate'],titleline)
    if len(RVEparams['steps'])>1:
        createCSVfile(RVEparams['output']['global']['directory'],RVEparams['output']['global']['filenames']['thermalenergyreleaserate'],titleline)

    skipLineToLogFile(logfilefullpath,'a',True)
    writeLineToLogFile(logfilefullpath,'a','In function: main(argv)',True)

    skipLineToLogFile(logfilefullpath,'a',True)
    writeLineToLogFile(logfilefullpath,'a',logindent + 'Global timer starts',True)
    globalStart = timeit.default_timer()

    for iterationSet in iterationsSets:

        timedataList = []
        totalIterationTime = 0.0
        variationString = ''
        for v,value in enumerate(iterationSet):
            if v>0:
                variationString += '-'
            variationString += str(sortedKeywords[v][-1]) + str(value).replace('.','_')
            fillDataDictionary(RVEparams,sortedKeywords[v],value)

        RVEparams['input']['modelname'] = basename + '_' + variationString

        if RVEparams['geometry']['deltatheta']<20:
            RVEparams['mesh']['size']['deltapsi'] = 0.5*RVEparams['geometry']['deltatheta']
            RVEparams['mesh']['size']['deltaphi'] = 20.0
        elif RVEparams['geometry']['deltatheta']<140:
            RVEparams['mesh']['size']['deltapsi'] = 10.0
            RVEparams['mesh']['size']['deltaphi'] = 20.0
        else:
            RVEparams['mesh']['size']['deltapsi'] = 0.4*(180.0-RVEparams['geometry']['deltatheta'])
            RVEparams['mesh']['size']['deltaphi'] = 0.4*(180.0-RVEparams['geometry']['deltatheta'])

        RVEparams['output']['local']['directory'] = join(RVEparams['output']['global']['directory'],RVEparams['input']['modelname'])
        RVEparams['output']['local']['filenames']['Jintegral'] = RVEparams['input']['modelname'] + '-Jintegral'
        RVEparams['output']['local']['filenames']['stressesatboundary'] = RVEparams['input']['modelname'] + '-stressesatboundary'
        RVEparams['output']['local']['filenames']['stressesatsymmetryline'] = RVEparams['input']['modelname'] + '-stressesatsymmetryline'
        RVEparams['output']['local']['filenames']['stressesatbondedinterface'] = RVEparams['input']['modelname'] + '-stressesatbondedinterface'
        RVEparams['output']['local']['filenames']['crackdisplacements'] = RVEparams['input']['modelname'] + '-crackdisplacements'
        RVEparams['output']['local']['filenames']['contactzonetolerance'] = RVEparams['input']['modelname'] + '-contactzonetol'

        RVEparams['output']['report']['local']['directory'].append(join(RVEparams['output']['global']['directory'],RVEparams['input']['modelname']))
        RVEparams['output']['report']['local']['filenames']['Jintegral'].append(RVEparams['input']['modelname'] + '-Jintegral')
        RVEparams['output']['report']['local']['filenames']['stressesatboundary'].append(RVEparams['input']['modelname'] + '-stressesatboundary')
        RVEparams['output']['report']['local']['filenames']['crackdisplacements'].append(RVEparams['input']['modelname'] + '-crackdisplacements')
        RVEparams['output']['report']['local']['filenames']['contactzonetolerance'].append(RVEparams['input']['modelname'] + '-contactzonetol')

        appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['local']['directory'],RVEparams['output']['local']['filenames']['Jintegral']+'.csv'),'Jintegral-Params='+variationString,RVEparams['plot']['local']['Jintegral']['toPlot'],RVEparams['plot']['local']['Jintegral']['variables']]])
        appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['local']['directory'],RVEparams['output']['local']['filenames']['stressesatboundary']+'.csv'),'StressAtBoundary-Params='+variationString,RVEparams['plot']['local']['stressatboundary']['toPlot'],RVEparams['plot']['local']['stressatboundary']['variables']]])
        appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['local']['directory'],RVEparams['output']['local']['filenames']['stressesatsymmetryline']+'.csv'),'StressAtSymmLine-Params='+variationString,RVEparams['plot']['local']['stressatsymmetryline']['toPlot'],RVEparams['plot']['local']['stressatsymmetryline']['variables']]])
        appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['local']['directory'],RVEparams['output']['local']['filenames']['stressesatbondedinterface']+'.csv'),'StressAtBondInter-Params='+variationString,RVEparams['plot']['local']['stressatbondedinterface']['toPlot'],RVEparams['plot']['local']['stressatbondedinterface']['variables']]])
        appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['local']['directory'],RVEparams['output']['local']['filenames']['crackdisplacements']+'.csv'),'CrackDisps-Params='+variationString,RVEparams['plot']['local']['crackdisplacements']['toPlot'],RVEparams['plot']['local']['crackdisplacements']['variables']]])
        appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['local']['directory'],RVEparams['output']['local']['filenames']['contactzonetolerance']+'.csv'),'TolCZ-Params='+variationString,RVEparams['plot']['local']['contactzonetolerance']['toPlot'],RVEparams['plot']['local']['contactzonetolerance']['variables']]])

        if len(RVEparams['steps'])>1:
            RVEparams['output']['local']['filenames']['thermalJintegral'] = RVEparams['input']['modelname'] + '-thermalJintegral'
            RVEparams['output']['local']['filenames']['thermalcrackdisplacements'] = RVEparams['input']['modelname'] + '-thermalcrackdisplacements'
            RVEparams['output']['local']['filenames']['thermalcontactzonetolerance'] = RVEparams['input']['modelname'] + '-thermalcontactzonetol'

            appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['local']['directory'],RVEparams['output']['local']['filenames']['thermalJintegral']+'.csv'),'thermalJintegral-Params='+variationString,RVEparams['plot']['local']['Jintegral']['toPlot'],RVEparams['plot']['local']['Jintegral']['variables']]])
            appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['local']['directory'],RVEparams['output']['local']['filenames']['thermalcrackdisplacements']+'.csv'),'thermalCrackDisps-Params='+variationString,RVEparams['plot']['local']['crackdisplacements']['toPlot'],RVEparams['plot']['local']['crackdisplacements']['variables']]])
            appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0].split('_')[-1] + '_csvfileslist',[[join(RVEparams['output']['local']['directory'],RVEparams['output']['local']['filenames']['thermalcontactzonetolerance']+'.csv'),'thermalTolCZ-Params='+variationString,RVEparams['plot']['local']['contactzonetolerance']['toPlot'],RVEparams['plot']['local']['contactzonetolerance']['variables']]])


        timedataList.append(RVEparams['input']['modelname'])

        if not os.path.exists(RVEparams['output']['local']['directory']):
                os.mkdir(RVEparams['output']['local']['directory'])

        #================= create ABAQUS CAE model
        skipLineToLogFile(logfilefullpath,'a',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Calling function: createRVE(parameters,logfilepath,baselogindent,logindent)',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer starts',True)
        localStart = timeit.default_timer()
        try:
            if RVEparams['simulation-pipeline']['create-CAE']:
                modelData = createRVE(RVEparams,logfilefullpath,logindent,logindent)
            localElapsedTime = timeit.default_timer() - localStart
            timedataList.append(localElapsedTime)
            totalIterationTime += localElapsedTime
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Successfully returned from function: createRVE(parameters,logfilepath,baselogindent,logindent)',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer stopped',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Elapsed time: ' + str(localElapsedTime) + ' [s]',True)
        except Exception, error:
            writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
            sys.exit(2)

        #================= modify input file
        skipLineToLogFile(logfilefullpath,'a',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Calling function: modifyRVEinputfile(parameters,mdbData,logfilepath,baselogindent,logindent)',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer starts',True)
        localStart = timeit.default_timer()
        try:
            if RVEparams['simulation-pipeline']['modify-INP']:
                inputfilename = modifyRVEinputfile(RVEparams,modelData,logfilefullpath,logindent,logindent)
            localElapsedTime = timeit.default_timer() - localStart
            timedataList.append(localElapsedTime)
            totalIterationTime += localElapsedTime
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Successfully returned from function: modifyRVEinputfile(parameters,mdbData,logfilepath,baselogindent,logindent)',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer stopped',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Elapsed time: ' + str(localElapsedTime) + ' [s]',True)
        except Exception, error:
            writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
            sys.exit(2)

        #================= run ABAQUS simulation
        skipLineToLogFile(logfilefullpath,'a',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Calling function: runRVEsimulation(wd,inpfile,ncpus,logfilepath,baselogindent,logindent)',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer starts',True)
        localStart = timeit.default_timer()
        try:
            if RVEparams['simulation-pipeline']['analyze-ODB']:
                runRVEsimulation(RVEparams['input']['wd'],inputfilename,RVEparams['solver']['cpus'],logfilefullpath,logindent,logindent)
            localElapsedTime = timeit.default_timer() - localStart
            timedataList.append(localElapsedTime)
            totalIterationTime += localElapsedTime
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Successfully returned from function: runRVEsimulation(wd,inpfile,ncpus,logfilepath,baselogindent,logindent)',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer stopped',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Elapsed time: ' + str(localElapsedTime) + ' [s]',True)
        except Exception, error:
            writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
            sys.exit(2)
        #inputfilename = 'Job-VCCTandJintegral-RVE100-Half-SmallDisplacement-Free-10' + '.inp'

        #================= extract and analyze data from ODB
        skipLineToLogFile(logfilefullpath,'a',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Calling function: analyzeRVEresults(wd,odbname,logfilepath,parameters)',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer starts',True)
        localStart = timeit.default_timer()
        try:
            if RVEparams['simulation-pipeline']['analyze-ODB']:
                analyzeRVEresults(inputfilename.split('.')[0]+'.odb',RVEparams,logfilefullpath,logindent,logindent)
            localElapsedTime = timeit.default_timer() - localStart
            timedataList.append(localElapsedTime)
            totalIterationTime += localElapsedTime
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Successfully returned from function: analyzeRVEresults(wd,odbname,logfilepath,parameters)',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer stopped',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Elapsed time: ' + str(localElapsedTime) + ' [s]',True)
        except Exception, error:
            writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
            sys.exit(2)

        timedataList.append(np.sum(timedataList[1:]))
        appendCSVfile(RVEparams['output']['global']['directory'],logfilename.split('.')[0] + '_TIME',[timedataList])

        if RVEparams['simulation-pipeline']['archive-ODB']:
            skipLineToLogFile(logfilefullpath,'a',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Moving ODB to archive... ',True)
            try:
                copyfile(join(RVEparams['input']['wd'],inputfilename.split('.')[0]+'.odb'),join(RVEparams['output']['archive']['directory'],inputfilename.split('.')[0]+'.odb'))
                os.remove(join(RVEparams['input']['wd'],inputfilename.split('.')[0]+'.odb'))
                writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)
            except Exception, error:
                writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
                sys.exc_clear()
        elif RVEparams['simulation-pipeline']['remove-ODB']:
            skipLineToLogFile(logfilefullpath,'a',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Remove .odb file from working directory... ',True)
            try:
                os.remove(join(RVEparams['input']['wd'],inputfilename.split('.')[0]+'.odb'))
                writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)
            except Exception, error:
                writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
                sys.exc_clear()

        if  RVEparams['simulation-pipeline']['remove-DAT']:
            skipLineToLogFile(logfilefullpath,'a',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Remove .dat file from working directory... ',True)
            try:
                os.remove(join(RVEparams['input']['wd'],inputfilename.split('.')[0]+'.dat'))
                writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)
            except Exception, error:
                writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
                sys.exc_clear()

        if  RVEparams['simulation-pipeline']['remove-PRT']:
            skipLineToLogFile(logfilefullpath,'a',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Remove .prt file from working directory... ',True)
            try:
                os.remove(join(RVEparams['input']['wd'],inputfilename.split('.')[0]+'.prt'))
                writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)
            except Exception, error:
                writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
                sys.exc_clear()

        if  RVEparams['simulation-pipeline']['remove-STA']:
            skipLineToLogFile(logfilefullpath,'a',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Remove .sta file from working directory... ',True)
            try:
                os.remove(join(RVEparams['input']['wd'],inputfilename.split('.')[0]+'.sta'))
                writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)
            except Exception, error:
                writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
                sys.exc_clear()

        if  RVEparams['simulation-pipeline']['remove-SIM']:
            skipLineToLogFile(logfilefullpath,'a',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Remove .sim file from working directory... ',True)
            try:
                os.remove(join(RVEparams['input']['wd'],inputfilename.split('.')[0]+'.sim'))
                writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)
            except Exception, error:
                writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
                sys.exc_clear()

        if  RVEparams['simulation-pipeline']['remove-MSG']:
            skipLineToLogFile(logfilefullpath,'a',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Remove .msg file from working directory... ',True)
            try:
                os.remove(join(RVEparams['input']['wd'],inputfilename.split('.')[0]+'.msg'))
                writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)
            except Exception, error:
                writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
                sys.exc_clear()

        if  RVEparams['simulation-pipeline']['remove-INP']:
            skipLineToLogFile(logfilefullpath,'a',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Remove .inp file from working directory... ',True)
            try:
                os.remove(join(RVEparams['input']['wd'],inputfilename.split('.')[0]+'.inp'))
                writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)
            except Exception, error:
                writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
                sys.exc_clear()

        if  RVEparams['simulation-pipeline']['remove-COM']:
            skipLineToLogFile(logfilefullpath,'a',True)
            writeLineToLogFile(logfilefullpath,'a',logindent + 'Remove .com file from working directory... ',True)
            try:
                os.remove(join(RVEparams['input']['wd'],inputfilename.split('.')[0]+'.com'))
                writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)
            except Exception, error:
                writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
                sys.exc_clear()

        if debug:
            break

    if RVEparams['simulation-pipeline']['archive-CAE']:
        skipLineToLogFile(logfilefullpath,'a',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Moving CAE to archive... ',True)
        try:
            copyfile(join(RVEparams['input']['wd'],RVEparams['input']['caefilename']+'.cae'),join(RVEparams['output']['archive']['directory'],RVEparams['input']['caefilename']+'.cae'))
            os.remove(join(RVEparams['input']['wd'],RVEparams['input']['caefilename']+'.cae'))
            writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)
        except Exception, error:
            writeErrorToLogFile(logfilefullpath,'a',Exception,error,True)
            sys.exc_clear()

    #=======================================================================
    # END - ANALYSIS
    #=======================================================================

    #=======================================================================
    # BEGIN - REPORTING
    #=======================================================================

    writeLineToLogFile(logfilefullpath,'a',logindent + '... done. ',True)
    if RVEparams['simulation-pipeline']['report-EXCEL']:
        skipLineToLogFile(logfilefullpath,'a',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Begin reporting in excel',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer starts',True)
        localStart = timeit.default_timer()
        codeFolder = 'D:/01_Luca/06_WD/thinPlyMechanics/python'
        if 'Windows' in system():
            writeLineToLogFile(logfilefullpath,'a',2*logindent + 'Create Windows command file',True)
            cmdfile = join(RVEparams['output']['global']['directory'],'dataToXlsx.cmd')
            with open(cmdfile,'w') as cmd:
                cmd.write('\n')
                cmd.write('CD ' + RVEparams['output']['global']['directory'] + '\n')
                cmd.write('\n')
                cmd.write('python ' + join(codeFolder,'reportData' + '.py') + ' -w ' + RVEparams['output']['global']['directory'] + ' -i ' + logfilename.split('.')[0].split('_')[-1] + '_csvfileslist' + '.csv' + ' -o ' + RVEparams['output']['global']['directory']  + ' -f ' + RVEparams['input']['caefilename'] + '.xlsx' + ' --excel ' + '\n')
            writeLineToLogFile(logfilefullpath,'a',2*logindent + 'Executing Windows command file...',True)
            try:
                subprocess.call('cmd.exe /C ' + cmdfile)
                writeLineToLogFile(logfilefullpath,'a',2*logindent + '... done.',True)
            except Exception,error:
                writeLineToLogFile(logfilefullpath,'a',2*logindent + 'ERROR',True)
                writeLineToLogFile(logfilefullpath,'a',2*logindent + str(Exception),True)
                writeLineToLogFile(logfilefullpath,'a',2*logindent + str(error),True)
                sys.exc_clear()
        elif 'Linux' in system():
            writeLineToLogFile(logfilefullpath,'a',2*logindent + 'Create Linux bash file',True)
            bashfile = join(RVEparams['output']['global']['directory'],'dataToXlsx.sh')
            with open(bashfile,'w') as bsh:
                bsh.write('#!/bin/bash\n')
                bsh.write('\n')
                bsh.write('cd ' + RVEparams['output']['global']['directory'] + '\n')
                bsh.write('\n')
                bsh.write('python ' + join(codeFolder,'reportData' + '.py') + ' -w ' + RVEparams['output']['global']['directory'] + ' -i ' + logfilename.split('.')[0].split('_')[-1] + '_csvfileslist' + '.csv' + ' -f ' + RVEparams['input']['caefilename'] + '.xlsx' + '\n')
                writeLineToLogFile(logfilefullpath,'a',2*logindent + 'Executing Linux bash file...',True)
                try:
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Change permissions to ' + bashfile ,True)
                    os.chmod(bashfile, 0o755)
                    writeLineToLogFile(logfilefullpath,'a','Run bash file',True)
                    call('.' + bashfile)
                    writeLineToLogFile(logfilefullpath,'a',2*logindent + '... done.',True)
                except Exception:
                    writeLineToLogFile(logfilefullpath,'a',2*logindent + 'ERROR',True)
                    writeLineToLogFile(logfilefullpath,'a',2*logindent + str(Exception),True)
                    writeLineToLogFile(logfilefullpath,'a',2*logindent + str(error),True)
                    sys.exc_clear()
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer stopped',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Elapsed time: ' + str(localElapsedTime) + ' [s]',True)

    if RVEparams['simulation-pipeline']['report-LATEX']:
        skipLineToLogFile(logfilefullpath,'a',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Begin reporting in latex',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer starts',True)
        localStart = timeit.default_timer()

        writeLineToLogFile(logfilefullpath,'a',logindent + 'Setting the locale to US english ... ',True)
        locale.setlocale(locale.LC_TIME,'us_US')
        writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)

        writeLineToLogFile(logfilefullpath,'a',logindent + 'Check if latex output directories exist and create them if needed ... ',True)

        reportFolder = RVEparams['output']['report']['global']['directory']
        reportFilename = RVEparams['output']['report']['global']['filename'].split('.')[0]

        if not os.path.exists(reportFolder):
                os.mkdir(reportFolder)

        if not os.path.exists(join(reportFolder,'pics')):
                os.mkdir(join(reportFolder,'pics'))

        writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)

        writeLineToLogFile(logfilefullpath,'a',logindent + 'Copy report template images to latex folder ... ',True)
        copyfile(join('D:/01_Luca/06_WD/thinPlyMechanics/tex/Templates/Template_reports','Docmase_logo.jpg'),join(reportFolder,'pics','Docmase_logo.jpg'))
        copyfile(join('D:/01_Luca/06_WD/thinPlyMechanics/tex/Templates/Template_reports','erasmusmundus_logo.jpg'),join(reportFolder,'pics','erasmusmundus_logo.jpg'))
        copyfile(join('D:/01_Luca/06_WD/thinPlyMechanics/tex/Templates/Template_slides','logo-eeigm.jpg'),join(reportFolder,'pics','logo-eeigm.jpg'))
        copyfile(join('D:/01_Luca/06_WD/thinPlyMechanics/tex/Templates/Template_reports','lulea_logo1.jpg'),join(reportFolder,'pics','lulea_logo1.jpg'))
        writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)

        writeLineToLogFile(logfilefullpath,'a',logindent + 'Reading index of generated csv files ... ',True)
        with open(join(RVEparams['output']['global']['directory'],logfilename.split('.')[0] + '_csvfileslist' + '.csv'),'r') as csv:
            lines = csv.readlines()
        writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)

        writeLineToLogFile(logfilefullpath,'a',logindent + 'Generating local plots ... ',True)
        for l,line in enumerate(lines[5:]):
            csvPath = line.replace('\n','').split(',')[0]
            outDir = csvPath.split('\\')[0] + '/' + csvPath.split('\\')[1]
            writeLineToLogFile(logfilefullpath,'a',2*logindent + 'Opening file ' + csvPath,True)
            with open(csvPath,'r') as csv:
                csvlines = csv.readlines()
            toPlot = bool(line.replace('\n','').split(',')[2])
            plotSettings = []
            if toPlot:
                stringToEval = ','.join(line.replace('\n','').split(',')[3:])
                plotSettings = ast.literal_eval(stringToEval[1:])
                writeLineToLogFile(logfilefullpath,'a',2*logindent + str(len(plotSettings)) + ' PLOTS REQUESTED',True)
                for p,plot in enumerate(plotSettings):
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Plot name: ' + plot[-1],True)
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'x-axis name: ' + plot[-3],True)
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'y-axis name: ' + plot[-2],True)
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Number of curves: ' + str(len(plot[:-3])),True)
                    xyData = []
                    legendEntries = ''
                    dataoptions = []
                    for c,curve in enumerate(plot[:-3]):
                        writeLineToLogFile(logfilefullpath,'a',4*logindent + '(' + str(c+1) + ') Curve name: ' + curve[2],True)
                        writeLineToLogFile(logfilefullpath,'a',4*logindent + '    x-values: ' + csvlines[0].replace('\n','').split(',')[int(curve[0])],True)
                        xData = []
                        for csvline in csvlines[1:]:
                            if len(csvline)>2:
                                xData.append(float(csvline.replace('\n','').split(',')[int(curve[0])]))
                        writeLineToLogFile(logfilefullpath,'a',4*logindent + '    y-values: ' + csvlines[0].replace('\n','').split(',')[int(curve[1])],True)
                        yData = []
                        for csvline in csvlines[1:]:
                            if len(csvline)>2:
                                yData.append(float(csvline.replace('\n','').split(',')[int(curve[1])]))
                        xyData.append(np.transpose([np.array(xData),np.array(yData)]))
                        if c>0:
                            legendEntries += ', '
                        legendEntries += '{$' + curve[2] + '$}'
                        dataoptions.append('red!' + str(100.0*float(c)/float(len(plot[:-3]))) + '!blue')
                    axisoptions = 'width=30cm,\n ' \
                                  'title={\\bf{' + plot[-1] + '}},\n ' \
                                  'title style={font=\\fontsize{40}{8}\\selectfont},\n ' \
                                  'xlabel style={at={(axis description cs:0.5,-0.02)},anchor=north,font=\\fontsize{44}{40}\\selectfont},\n ' \
                                  'ylabel style={at={(axis description cs:-0.025,.5)},anchor=south,font=\\fontsize{44}{40}\\selectfont},\n ' \
                                  'xlabel={$' + plot[-3] + '$},ylabel={$' + plot[-2] + '$},\n ' \
                                  'tick align=outside,\n ' \
                                  'tick label style={font=\\huge},\n ' \
                                  'xmajorgrids,\n ' \
                                  'x grid style={lightgray!92.026143790849673!black},\n ' \
                                  'ymajorgrids,\n ' \
                                  'y grid style={lightgray!92.026143790849673!black},\n ' \
                                  'line width=0.5mm,\n ' \
                                  'legend style={draw=white!80.0!black,font=\\fontsize{28}{24}\\selectfont,row sep=15pt},\n ' \
                                  'legend entries={' + legendEntries + '},\n ' \
                                  'legend image post style={xscale=2},\n ' \
                                  'legend cell align={left}'
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Create plot in file ' + plot[-1].replace(' ','-').replace('/','-').replace(',','') + '.pdf' + ' in directory ' + outDir,True)
                    writeLatexMultiplePlots(outDir,plot[-1].replace(' ','-').replace('/','-').replace(',','') + '.tex',xyData,axisoptions,dataoptions,logfilefullpath,3*logindent,logindent)
            else:
                writeLineToLogFile(logfilefullpath,'a',2*logindent + 'NO PLOT REQUESTED',True)

        writeLineToLogFile(logfilefullpath,'a',logindent + 'Generating global plots ... ',True)
        for l,line in enumerate(lines[1:5]):
            csvPath = line.replace('\n','').split(',')[0]
            outDir = csvPath.split('\\')[0]
            writeLineToLogFile(logfilefullpath,'a',2*logindent + 'Opening file ' + csvPath,True)
            with open(csvPath,'r') as csv:
                csvlines = csv.readlines()
            plotName = line.replace('\n','').split(',')[1]
            toPlot = bool(line.replace('\n','').split(',')[2])
            plotSettings = []
            if toPlot:
                stringToEval = ','.join(line.replace('\n','').split(',')[3:])
                plotSettings = ast.literal_eval(stringToEval[1:])
                writeLineToLogFile(logfilefullpath,'a',2*logindent + str(len(plotSettings)) + ' PLOTS REQUESTED',True)
                for p,plot in enumerate(plotSettings):
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Plot name: ' + plot[-1],True)
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'x-axis name: ' + plot[-3],True)
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'y-axis name: ' + plot[-2],True)
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Number of curves: ' + str(len(plot[:-3])),True)
                    xyData = []
                    legendEntries = ''
                    dataoptions = []
                    for c,curve in enumerate(plot[:-3]):
                        writeLineToLogFile(logfilefullpath,'a',4*logindent + '(' + str(c+1) + ') Curve name: ' + curve[2],True)
                        writeLineToLogFile(logfilefullpath,'a',4*logindent + '    x-values: ' + csvlines[0].replace('\n','').split(',')[int(curve[0])],True)
                        xData = []
                        for csvline in csvlines[1:]:
                            if len(csvline)>2:
                                xData.append(float(csvline.replace('\n','').split(',')[int(curve[0])]))
                        writeLineToLogFile(logfilefullpath,'a',4*logindent + '    y-values: ' + csvlines[0].replace('\n','').split(',')[int(curve[1])],True)
                        yData = []
                        for csvline in csvlines[1:]:
                            if len(csvline)>2:
                                yData.append(float(csvline.replace('\n','').split(',')[int(curve[1])]))
                        xyData.append(np.transpose([np.array(xData),np.array(yData)]))
                        if c>0:
                            legendEntries += ', '
                        legendEntries += '{$' + curve[2] + '$}'
                        dataoptions.append('red!' + str(100.0*float(c)/float(len(plot[:-3]))) + '!blue')
                    axisoptions = 'width=30cm,\n ' \
                                  'title={\\bf{' + plot[-1] + '}},\n ' \
                                  'title style={font=\\fontsize{40}{8}\\selectfont},\n ' \
                                  'xlabel style={at={(axis description cs:0.5,-0.02)},anchor=north,font=\\fontsize{44}{40}\\selectfont},\n ' \
                                  'ylabel style={at={(axis description cs:-0.025,.5)},anchor=south,font=\\fontsize{44}{40}\\selectfont},\n ' \
                                  'xlabel={$' + plot[-3] + '$},ylabel={$' + plot[-2] + '$},\n ' \
                                  'tick align=outside,\n ' \
                                  'tick label style={font=\\huge},\n ' \
                                  'xmajorgrids,\n ' \
                                  'x grid style={lightgray!92.026143790849673!black},\n ' \
                                  'ymajorgrids,\n ' \
                                  'y grid style={lightgray!92.026143790849673!black},\n ' \
                                  'line width=0.5mm,\n ' \
                                  'legend style={draw=white!80.0!black,font=\\fontsize{28}{24}\\selectfont,row sep=15pt},\n ' \
                                  'legend entries={' + legendEntries + '},\n ' \
                                  'legend image post style={xscale=2},\n ' \
                                  'legend cell align={left}'
                    writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Create plot in file ' + plot[-1].replace(' ','-').replace('/','-').replace(',','') + '.pdf' + ' in directory ' + outDir,True)
                    writeLatexMultiplePlots(outDir,plot[-1].replace(' ','-').replace('/','-').replace(',','') + '.tex',xyData,axisoptions,dataoptions,logfilefullpath,3*logindent,logindent)
            else:
                writeLineToLogFile(logfilefullpath,'a',2*logindent + 'NO PLOT REQUESTED',True)

        writeLineToLogFile(logfilefullpath,'a',logindent + '... done.',True)

        writeLineToLogFile(logfilefullpath,'a',logindent + 'Creating main report ...',True)

        writeLineToLogFile(logfilefullpath,'a',2*logindent + 'Create latex file ...',True)
        createLatexFile(reportFolder,reportFilename,'scrartcl',options='a4paper, twoside,12pt, abstract')
        packages = ['inputenc',
                    'fontenc',
                    'amsfonts',
                    'amsmath',
                    'amssymb',
                    'amstext',
                    'animate',
                    'babel',
                    'biblatex',
                    'bm',
                    'booktabs',
                    'caption',
                    'colortbl',
                    'csquotes',
                    'enumerate',
                    'eurosym',
                    'geometry',
                    'graphicx',
                    'float',
                    'helvet',
                    'longtable',
                    'makeidx',
                    'multirow',
                    'nameref',
                    'parskip',
                    'pdfpages',
                    'rotating',
                    'scrpage2',
                    'setspace',
                    'standalone',
                    'subcaption',
                    'tabularx',
                    'tikz',
                    'xcolor',
                    'glossaries',
                    'hyperref']
        options = ['utf8',
                   'fontenc',
                   '',
                   '',
                   '',
                   '',
                   '',
                   'english',
                   'backend=bibtex, sorting=none,style=numeric',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   'right',
                   'inner=3cm,outer=2cm,top=2.7cm,bottom=3.2cm',
                   '',
                   '',
                   'scaled=.90',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   '',
                   'acronym,nonumberlist,nopostdot,toc',
                   '']
        writeLatexPackages(reportFolder,reportFilename,packages,options)
        writeLineToLogFile(logfilefullpath,'a',2*logindent + '... done.',True)

        writeLineToLogFile(logfilefullpath,'a',2*logindent + 'Write packages ...',True)
        writeLatexCustomLine(reportFolder,reportFilename,'\\definecolor{Gray}{gray}{0.85}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\definecolor{LightCyan}{rgb}{0.88,1,1}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\sloppy % avoids lines that are too long on the right side')
        writeLatexCustomLine(reportFolder,reportFilename,'% avoid "orphans"')
        writeLatexCustomLine(reportFolder,reportFilename,'\\clubpenalty = 10000')
        writeLatexCustomLine(reportFolder,reportFilename,'% avoid "widows"')
        writeLatexCustomLine(reportFolder,reportFilename,'\\widowpenalty = 10000')
        writeLatexCustomLine(reportFolder,reportFilename,'% this makes the table of content etc. look better')
        writeLatexCustomLine(reportFolder,reportFilename,'\\renewcommand{\\dotfill}{\\leaders\\hbox to 5pt{\\hss.\\hss}\\hfill}')
        writeLatexCustomLine(reportFolder,reportFilename,'% avoid indentation of line after a paragraph')
        writeLatexSetLength(reportFolder,reportFilename,'parindent','0pt')
        writeLatexGenericCommand(reportFolder,reportFilename,'pagestyle','','scrheadings')
        writeLatexGenericCommand(reportFolder,reportFilename,'automark','section','section')
        writeLatexGenericCommand(reportFolder,reportFilename,'ofoot','','\\pagemark')
        writeLatexGenericCommand(reportFolder,reportFilename,'ifoot','','Research Plan')
        writeLatexSetLength(reportFolder,reportFilename,'unitlength','1cm')
        writeLatexSetLength(reportFolder,reportFilename,'oddsidemargin','0.3cm')
        writeLatexSetLength(reportFolder,reportFilename,'evensidemargin','0.3cm')
        writeLatexSetLength(reportFolder,reportFilename,'textwidth','15.5cm')
        writeLatexSetLength(reportFolder,reportFilename,'topmargin','0cm')
        writeLatexSetLength(reportFolder,reportFilename,'textheight','22cm')
        writeLatexCustomLine(reportFolder,reportFilename,'\\columnsep 0.5cm')
        writeLatexCustomLine(reportFolder,reportFilename,'\\newcommand{\\brac}[1]{\\left(#1\\right)}')
        writeLatexGenericCommand(reportFolder,reportFilename,'graphicspath','','{./pics/}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\addto\\captionsenglish{\\renewcommand{\\listfigurename}{Figures}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\addto\\captionsenglish{\\renewcommand{\\listtablename}{Tables}}')
        writeLatexGenericCommand(reportFolder,reportFilename,'makeglossaries','','')
        writeLatexGenericCommand(reportFolder,reportFilename,'makeindex','','',)
        writeLineToLogFile(logfilefullpath,'a',2*logindent + '... done.',True)

        writeLineToLogFile(logfilefullpath,'a',2*logindent + 'Document starts ...',True)

        writeLatexDocumentStarts(reportFolder,reportFilename)

        writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Title page',True)

        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%                  Front Matter                  %')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%                 Title Page')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\clearscrheadings')
        writeLatexCustomLine(reportFolder,reportFilename,'\\pagestyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\manualmark')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ihead{\\href{http://www.ltu.se/}{\\includegraphics[height=1.5cm]{lulea_logo1.jpg}}\\hspace{6.1953125cm}\\href{http://www.eeigm.univ-lorraine.fr/}{\\includegraphics[height=1.5cm]{logo-eeigm.jpg}}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ifoot{\\noindent\\makebox[\\linewidth]{\\rule{\\textwidth}{0.4pt}}\\\\\\href{http://eacea.ec.europa.eu/erasmus_mundus/index_en.php}{\\includegraphics[height=1.75cm]{erasmusmundus_logo.jpg}}\\hspace{9.55cm}\\href{http://www.uni-saarland.de/einrichtung/eusmat/international-studies/phd/docmase.html}{\\includegraphics[height=1.75cm]{Docmase_logo.jpg}}}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\begin{center}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\vspace*{0.1cm}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\begin{Large}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\textbf{\\textsc{EUSMAT}}\\\\[0.75ex]')
        writeLatexCustomLine(reportFolder,reportFilename,'\\end{Large}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\begin{large}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\textbf{European School of Materials}\\\\[0.75ex]')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\vspace*{1cm}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\textbf{DocMASE}\\\\[0.75ex]')
        writeLatexCustomLine(reportFolder,reportFilename,'\\textbf{\\textsc{Doctorate in Materials Science and Engineering}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\end{large}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\vspace{1.75cm}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\begin{Large}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\textbf{\\textsc{Simulation Report}}\\\\[0.75ex]')
        writeLatexCustomLine(reportFolder,reportFilename,'\\end{Large}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\vspace*{0.5cm}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\begin{LARGE}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\textbf{\\textsc{Report of ABAQUS simulations}}\\\\[0.75ex]')
        writeLatexCustomLine(reportFolder,reportFilename,'\\end{LARGE}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\vspace*{2.5cm}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\begin{flushright}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\begin{tabular}{l l }')
        writeLatexCustomLine(reportFolder,reportFilename,'{\\large \\textbf{Doctoral Candidate:}} & {\\large \\href{http://lucadistasioengineering.com/}{Luca DI STASIO}}\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'&\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'&\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'&\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'{\\large \\textbf{Thesis Supervisors:}}& {\\large Prof. Zoubir AYADI}\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'&{\\large Universit\\\'e de Lorraine}\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'&{\\large Nancy, France}\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'&\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'& {\\large Prof. Janis VARNA}\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'&{\\large Lule\\aa\\ University of Technology}\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'&{\\large Lule\\aa, Sweden}\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'\\end{tabular}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\end{flushright}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\vspace*{2cm}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        timeNow = datetime.now()
        writeLatexCustomLine(reportFolder,reportFilename,'{\\large \\textbf{Created on ' + timeNow.strftime('%B') + timeNow.strftime('%d') + ', ' + timeNow.strftime('%Y') +'}}\\\\[10pt]')
        writeLatexCustomLine(reportFolder,reportFilename,'{\\large \\textbf{Last Updated on \\today}}\\\\')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\end{center}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\cleardoublepage')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Table of Contents',True)
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%            Table of Contents')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\pagenumbering{roman}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setcounter{page}{1}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\clearscrheadings')
        writeLatexCustomLine(reportFolder,reportFilename,'\\pagestyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\manualmark')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ofoot{\\\\ \\hyperref[sec:content]{\\pagemark}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ifoot{} % ofoo')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ohead{\\contentsname}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadtopline{2pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setfootsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\tableofcontents')
        writeLatexCustomLine(reportFolder,reportFilename,'\\label{sec:content}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\cleardoublepageusingstyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLineToLogFile(logfilefullpath,'a',3*logindent + 'List of Figures',True)
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%            List of Figures')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\clearscrheadings')
        writeLatexCustomLine(reportFolder,reportFilename,'\\pagestyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\manualmark')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ofoot{\\\\ \\hyperref[sec:content]{\\pagemark}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ifoot{} % ofoo')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ohead{\\listfigurename}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadtopline{2pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setfootsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'%\\section*{List of Figures}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\addcontentsline{toc}{section}{\\listfigurename}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\listoffigures')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\cleardoublepageusingstyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLineToLogFile(logfilefullpath,'a',3*logindent + 'List of Tables',True)
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%            List of Tables')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\clearscrheadings')
        writeLatexCustomLine(reportFolder,reportFilename,'\\pagestyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\manualmark')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ofoot{\\\\ \\hyperref[sec:content]{\\pagemark}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ifoot{} % ofoo')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ohead{\\listtablename}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadtopline{2pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setfootsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'%\\section*{List of Tables}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\addcontentsline{toc}{section}{\\listtablename}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\listoftables')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\cleardoublepageusingstyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLineToLogFile(logfilefullpath,'a',3*logindent + 'List of Acronyms',True)
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%            List of Acronyms')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\clearscrheadings')
        writeLatexCustomLine(reportFolder,reportFilename,'\\pagestyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\manualmark')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ofoot{\\\\ \\hyperref[sec:content]{\\pagemark}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ifoot{} % ofoo')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ohead{\\nameref{sec:acr}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadtopline{2pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setfootsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\section*{Acronyms}\\label{sec:acr}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\addcontentsline{toc}{section}{\\nameref{sec:acr}}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\printglossary[type=\\acronymtype]')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'%\\printglossary')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\cleardoublepageusingstyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLineToLogFile(logfilefullpath,'a',3*logindent + 'List of Symbols',True)
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%            List of Symbols')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\clearscrheadings')
        writeLatexCustomLine(reportFolder,reportFilename,'\\pagestyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\manualmark')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ofoot{\\\\ \\hyperref[sec:content]{\\pagemark}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ifoot{} % ofoo')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ohead{\\nameref{sec:sym}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadtopline{2pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setfootsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\section*{Symbols}\\label{sec:sym}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\addcontentsline{toc}{section}{\\nameref{sec:sym}}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'%\\input{symbols}')
        writeLatexCustomLine(reportFolder,reportFilename,'%')
        writeLatexCustomLine(reportFolder,reportFilename,'\\cleardoublepageusingstyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Abstract',True)
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%                   Abstract')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\clearscrheadings')
        writeLatexCustomLine(reportFolder,reportFilename,'\\pagestyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\manualmark')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ofoot{\\\\ \\hyperref[sec:content]{\\pagemark}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ifoot{} % ofoo')
        writeLatexCustomLine(reportFolder,reportFilename,'\\ohead{\\nameref{sec:abs}}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadtopline{2pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setheadsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setfootsepline{0.5pt}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\section*{Abstract}\\label{sec:abs}')
        writeLatexCustomLine(reportFolder,reportFilename,'\\addcontentsline{toc}{section}{\\nameref{sec:abs}}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\cleardoublepageusingstyle{scrheadings}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%                   Main Matter                  %')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\pagenumbering{arabic}')
        writeLatexCustomLine(reportFolder,reportFilename,'')
        writeLatexCustomLine(reportFolder,reportFilename,'\\setcounter{page}{1}')
        writeLatexCustomLine(reportFolder,reportFilename,'')

        writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Global results',True)
        for l,line in enumerate(lines[1:5]):
            csvPath = line.replace('\n','').split(',')[0]
            outDir = csvPath.split('\\')[0]
            writeLineToLogFile(logfilefullpath,'a',4*logindent + 'Opening file ' + csvPath,True)
            with open(csvPath,'r') as csv:
                csvlines = csv.readlines()
            plotName = line.replace('\n','').split(',')[1]
            toPlot = bool(line.replace('\n','').split(',')[2])
            plotSettings = []
            if toPlot:
                writeLineToLogFile(logfilefullpath,'a',4*logindent + str(len(plotSettings)) + ' PLOTS TO BE INSERTED',True)
                plotSettings = ast.literal_eval(','.join(line.replace('\n','').split(',')[3:]))
                for p,plot in enumerate(plotSettings):
                    writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
                    writeLatexCustomLine(reportFolder,reportFilename,'%               GLOBAL - ' + plot[-1])
                    writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
                    writeLatexCustomLine(reportFolder,reportFilename,'')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\clearscrheadings')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\pagestyle{scrheadings}')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\manualmark')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\ofoot{\\\\ \\hyperref[sec:content]{\\pagemark}}')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\ifoot{} % ofoo')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\ohead{\\nameref{sec:sec1}}')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\setheadtopline{2pt}')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\setheadsepline{0.5pt}')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\setfootsepline{0.5pt}')
                    writeLatexCustomLine(reportFolder,reportFilename,'')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\section{Parametric study: ' + plot[-1] + '}\label{sec:sec1}')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\begin{figure}[!h]')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\includegraphics[width=\\textwidth]{' + outDir + plot[-1].replace(' ','-').replace('/','-').replace(',','') + '.pdf}')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\end{figure}')
                    writeLatexCustomLine(reportFolder,reportFilename,'')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\cleardoublepageusingstyle{scrheadings}')
                    writeLatexCustomLine(reportFolder,reportFilename,'')

        writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Local results',True)
        for l,line in enumerate(lines[5:]):
            csvPath = line.replace('\n','').split(',')[0]
            outDir = csvPath.split('\\')[0] + '/' + csvPath.split('\\')[1]
            writeLineToLogFile(logfilefullpath,'a',4*logindent + 'Opening file ' + csvPath,True)
            with open(csvPath,'r') as csv:
                csvlines = csv.readlines()
            plotName = line.replace('\n','').split(',')[1]
            toPlot = bool(line.replace('\n','').split(',')[2])
            plotSettings = []
            if toPlot:
                writeLineToLogFile(logfilefullpath,'a',4*logindent + str(len(plotSettings)) + ' PLOTS TO BE INSERTED',True)
                plotSettings = ast.literal_eval(','.join(line.replace('\n','').split(',')[3:]))
                writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
                writeLatexCustomLine(reportFolder,reportFilename,'%               SIMULATION N. ' + str(p+1))
                writeLatexCustomLine(reportFolder,reportFilename,'%------------------------------------------------%')
                writeLatexCustomLine(reportFolder,reportFilename,'')
                writeLatexCustomLine(reportFolder,reportFilename,'\\clearscrheadings')
                writeLatexCustomLine(reportFolder,reportFilename,'\\pagestyle{scrheadings}')
                writeLatexCustomLine(reportFolder,reportFilename,'\\manualmark')
                writeLatexCustomLine(reportFolder,reportFilename,'\\ofoot{\\\\ \\hyperref[sec:content]{\\pagemark}}')
                writeLatexCustomLine(reportFolder,reportFilename,'\\ifoot{} % ofoo')
                writeLatexCustomLine(reportFolder,reportFilename,'\\ohead{\\nameref{sec:sec1}}')
                writeLatexCustomLine(reportFolder,reportFilename,'\\setheadtopline{2pt}')
                writeLatexCustomLine(reportFolder,reportFilename,'\\setheadsepline{0.5pt}')
                writeLatexCustomLine(reportFolder,reportFilename,'\\setfootsepline{0.5pt}')
                writeLatexCustomLine(reportFolder,reportFilename,'')
                writeLatexCustomLine(reportFolder,reportFilename,'\\section{Simulation n. ' + str(p+1) + '}\label{sec:sec1}')
                for p,plot in enumerate(plotSettings):
                    writeLatexCustomLine(reportFolder,reportFilename,'\\begin{figure}[!h]')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\includegraphics[width=\\textwidth]{' + outDir + plot[-1].replace(' ','-').replace('/','-').replace(',','') + '.pdf}')
                    writeLatexCustomLine(reportFolder,reportFilename,'\\end{figure}')
                writeLatexCustomLine(reportFolder,reportFilename,'')
                writeLatexCustomLine(reportFolder,reportFilename,'\\cleardoublepageusingstyle{scrheadings}')
                writeLatexCustomLine(reportFolder,reportFilename,'')

        writeLineToLogFile(logfilefullpath,'a',3*logindent + 'Documents ends',True)
        writeLatexDocumentEnds(reportFolder,reportFilename)

        writeLineToLogFile(logfilefullpath,'a',2*logindent + '... done. ',True)

        writeLineToLogFile(logfilefullpath,'a',2*logindent + 'Compile pdf ... ',True)
        cmdfile = join(reportFolder,'runlatex.cmd')
        with open(cmdfile,'w') as cmd:
            cmd.write('\n')
            cmd.write('CD ' + reportFolder + '\n')
            cmd.write('\n')
            cmd.write('pdflatex ' + join(reportFolder,reportFilename.split(',')[0] + '.tex') + ' -job-name=' + reportFilename.split(',')[0] + '\n')
        try:
            subprocess.call('cmd.exe /C ' + cmdfile)
        except Exception:
            sys.exc_clear()
        writeLineToLogFile(logfilefullpath,'a',2*logindent + '... done. ',True)

        writeLineToLogFile(logfilefullpath,'a',logindent + 'Local timer stopped',True)
        writeLineToLogFile(logfilefullpath,'a',logindent + 'Elapsed time: ' + str(localElapsedTime) + ' [s]',True)

        writeLineToLogFile(logfilefullpath,'a',logindent + '... done. ',True)

    #=======================================================================
    # END - REPORTING
    #=======================================================================

    globalElapsedTime = timeit.default_timer() - globalStart
    writeLineToLogFile(logfilefullpath,'a',logindent + 'Global timer stopped',True)
    writeLineToLogFile(logfilefullpath,'a',logindent + 'Elapsed time: ' + str(globalElapsedTime) + ' [s]',True)

    skipLineToLogFile(logfilefullpath,'a',True)
    writeLineToLogFile(logfilefullpath,'a','Exiting function: main(argv)',True)
    writeLineToLogFile(logfilefullpath,'a','Goodbye!',True)

if __name__ == "__main__":
    main(sys.argv[1:])
