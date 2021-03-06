function[]=writeABQfullydebondedinterface(logfullfile,inpfullfile,numFiber,padlength,frictionLess,interfaceFriction)
%%
%==============================================================================
% Copyright (c) 2016 - 2017 Université de Lorraine & Luleå tekniska universitet
% Author: Luca Di Stasio <luca.distasio@gmail.com>
%                        <luca.distasio@ingpec.eu>
%
% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are met:
%
%
% Redistributions of source code must retain the above copyright
% notice, this list of conditions and the following disclaimer.
% Redistributions in binary form must reproduce the above copyright
% notice, this list of conditions and the following disclaimer in
% the documentation and/or other materials provided with the distribution
% Neither the name of the Université de Lorraine & Luleå tekniska universitet
% nor the names of its contributors may be used to endorse or promote products
% derived from this software without specific prior written permission.
%
% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
% AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
% IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
% ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
% LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
% CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
% SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
% INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
% CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
% ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
% POSSIBILITY OF SUCH DAMAGE.
%==============================================================================
%
%  DESCRIPTION
%
%  A function to generate FEM models of RVEs with ABAQUS, here space
%  dimension selection takes place
%
%  Output:
%
%%
writeToLogFile(logfullfile,'In function: writeABQfullydebondedinterface\n')
writeToLogFile(logfullfile,'\nStarting timer\n')
start = tic;

writeABQsurface(abqpath,['FiberSurface-Fiber',pad(num2str(i),numFibers,'left','0')],'none','none','none','none','none','none','none','none','NODE','none','none','none','none',...
                          {['NODES-ANNULUS-EXTINTERFACE-FIBER',pad(num2str(numFiber),numFibers,'left','0')]},'Fiber surface');
writeABQsurface(abqpath,['MatrixInterfaceSurface-Fiber',pad(num2str(i),numFibers,'left','0')],'none','none','none','none','none','none','none','none','NODE','none','none','none','none',...
                          {['NODES-ANNULUS-INTINTERFACE-MATRIX',pad(num2str(numFiber),numFibers,'left','0')]},'Matrix surface at fiber interface');
% contact interaction
writeABQcontactpair(abqpath,['FiberMatrixInterfaceInteraction-Fiber',pad(num2str(i),numFibers,'left','0')],'none','none','none','none','none','none','none','none','none','none','none','none','none','NODE TO SURFACE',...
                             {['MatrixInterfaceSurface-Fiber',pad(num2str(i),numFibers,'left','0'),', FiberSurface-Fiber',pad(num2str(i),numFibers,'left','0')]},'slave, master');
writeABQsurfaceinteraction(abqpath,['FiberMatrixInterfaceInteraction-Fiber',pad(num2str(i),numFibers,'left','0')],'none','none','none','none','none','none',{'1.0'},'Out-of-plane thickness of the surface');
if ~frictionLess>0
    writeABQfriction(abqpath,'none','none','none','0.005','none','none','none','none','none','none','none','none','none',{num2str(interfaceFriction, '%10.5e')},'friction coefficient');
end

elapsed = toc(start);
writeToLogFile(logfullfile,'Timer stopped.\n')
writeToLogFile(logfullfile,['\nELAPSED WALLCLOCK TIME: ', num2str(elapsed),' [s]\n\n'])
writeToLogFile(logfullfile,'Exiting function: writeABQfullydebondedinterface\n')

return
