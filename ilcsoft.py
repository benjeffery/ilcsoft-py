#!/usr/bin/python
import os,sys,time

# ILC software installation script
# Kristian Harder, k.harder@rl.ac.uk

# things not building properly:
#  - root does not link with cernlib (g77 vs gfort problems)
#
# additional packages?
#  - install important HEP plugins for jas3 rightaway?
#  - lccd
#  - SliC?
#  - SGV?
#  - brahms?
#
#
# check for libraries: - freeglut
#                      - gl (mesa, opengl?)
#                      - motif (openmotif/lesstif?)
# (check for header files too!)

######################
# configuration
######################

# packages that you do not want to (re-)install should be assigned to
# the skip map instead of the install map, i.e. replace the "install"
# in the corresponding line by a "skip"
install = {}
skip    = {}
#
install["python"]    =["2.5.2"]
install["swig"]      =["1.3.34"]
install["cmakemods"] =["v01-05-01"]
install["pythia"]    =["6.4.10"]
install["ccvssh"]    =["0.9.1-mod"]
install["cmake"]     =["2.4.6"]
install["maven"]     =["2.0.7"]
install["clhep"]     =["2.0.3.2"]
install["jaida"]     =["3.3.0-5"]
install["aidajni"]   =["3.2.6"]
install["lcio"]      =["v01-09"]
install["root"]      =["v5.14.00g"]
install["raida"]     =["HEAD"]  # HEAD instead of v01-03: fix unitialized values
install["gear"]      =["v00-08"]
install["geant"]     =["4.9.1"]
install["mokka"]     =["HEAD"]  # HEAD version to get latest test drivers
install["gsl"]       =["1.10"]
install["heppdt"]    =["3.02.03"]
install["lapack"]    =["3.1.1"]
install["cernlib"]   =["2006"]
install["marlin"]    =["HEAD"]  # fixes wrt v00-09-10 for better memory handling
install["marlinutil"]=["v00-06"]
install["boost"]     =["1_34_1"]
install["marlinreco"]=["HEAD"]  # memory leak fixes in TPCDigiProcessor
install["sidigi"]    =["v00-04"]
install["ced"]       =["v00-03"]
install["lcfivertex"]=["HEAD"]  # RPCutProcessor fixes
install["pandorapfa"]=["v02-00-01"]
install["jas3"]      =["0.8.4rc3"]


# installation order - don't touch this, even when not installing some of these
order = ["python","swig","ccvssh","cmakemods","pythia","cmake","maven","clhep",\
         "jaida","aidajni","lcio","root","raida",\
         "gear","geant","mokka","gsl","heppdt","lapack","cernlib",\
         "marlin","marlinutil","boost","marlinreco","sidigi","ced",\
         "lcfivertex","pandorapfa","jas3"]

######################
# installation options
######################

ilcbasedir="/ilc"
tardir=ilcbasedir+"/tarfiles"
USE_RAIDA=1
python_bindings = True
setupfile="ilcsetup"
arch="Linux-g++"
makeopts="-j 2"

# if this is set, as many programs will be compiled in debug mode as possible
debugmode=1


######################
# helper routines
######################

def eval(value):
    # parse environment variables
    return os.popen("echo "+value).readlines()[0].strip()

def set_environment(key, value, writeout=1):
    os.putenv(key, eval(value))
    if writeout:
        env=open(ilcbasedir+"/"+setupfile+".sh","a")
        env.write("export %s=%s\n"%(key,value))
        env.close()
        env=open(ilcbasedir+"/"+setupfile+".csh","a")
        env.write("setenv %s %s\n"%(key,value))

def exe(prefix,workdir,command,failmessage=""):
    # if a working directory is specified, make sure it exists
    if workdir!="" and not os.path.isdir(workdir):
        os.mkdir(workdir)
    # commands not associated with a specific part of the installation
    # will be logged on screen, all others will be logged in logfile
    if prefix!="":
        log=open(logfile,"a")
    else:
        log=sys.stdout
    log.write("%s==========COMMAND: %s\n"%(prefix,command))
    if prefix!="":
        log.close()
    # run the actual command in working directory and record exit value
    if workdir!="":
        [stdin,stdout]=os.popen4("cd "+workdir+";"+command+"; echo $?")
    else:
        [stdin,stdout]=os.popen4(command+"; echo $?")
    result=stdout.readlines()
    # log result
    if prefix!="":
        log=open(logfile,"a")
    else:
        log=sys.stdout
    for line in result:
        log.write("%s: %s"%(prefix,line))
    # check for non-zero output value and abort program upon error
    if result[-1][0]!="0":
        if failmessage=="":
            failmessage="%s ERROR --- aborting"%prefix
        log.write("%s\n"%failmessage)
        if workdir!="":
            log.write("%s workdir was %s\n"%(prefix,workdir))
        else:
            log.write("no workdir was specified for this command")
        log.close()
        if prefix!="":
            print failmessage
        sys.exit(1)
    if prefix!="":
        log.close()

def wget(id,workdir,url,localname=""):
    if localname=="":
        localname=url.split("/")[-1]
    exe(id,workdir,"wget -q -r \""+url+"\" -O "+localname)

def log(message):
    print message
    log=open(logfile,"a")
    log.write("+++++++++++++++++++++++++++++++\n")
    log.write("++++ "+message+"\n")
    log.write("+++++++++++++++++++++++++++++++\n")
    log.close()


######################
# installation details
######################


def install_cmakemods(version,doit):

    # set up environment
    workdir=ilcbasedir+"/cmakemodules-"+version
    set_environment("CVS_RSH","${DESY_CCVSSH}")
    set_environment("CMAKE_MODULE_PATH",workdir)
    if not doit: return

    # get code
    set_environment("CVSROOT",":ext:anonymous:@cvssrv.ifh.de:/ilctools",0)
    id="cmakemodules-"+version
    exe(id,workdir,"${DESY_CCVSSH} login")
    set_environment("CVSROOT",":ext:anonymous@cvssrv.ifh.de:/ilctools",0)
    exe(id,ilcbasedir,"cvs co -d "+workdir.split("/")[-1]\
        +" -r "+version+" CMakeModules")



def install_pythia(version,doit):

    # requirements:
    # - f77
    # - ar
    # - make

    # environment variables
    workdir=ilcbasedir+"/pythiabin"
    set_environment("PATH","${PATH}:"+workdir)
    if not doit: return
    
    # get Pythia code
    id="pythia-"+version
    wget(id,tardir,
         "http://www.hepforge.org/archive/pythia6/pythia-"+version+".tar.gz")
    # unpack and compile library
    libdir=ilcbasedir+"/pythialib-"+version
    exe(id,libdir,"tar zxf "+tardir+"/pythia-"+version+".tar.gz")
    exe(id,libdir,"make lib "+makeopts)
    # get and build example main program
    wget(id,workdir,
        "http://www-clued0.fnal.gov/~harderk/ilc/pythia/pythia_main.f")
    wget(id,workdir,
        "http://www-clued0.fnal.gov/~harderk/ilc/pythia/lcwrite.f")
    wget(id,workdir,
        "http://www-clued0.fnal.gov/~harderk/ilc/pythia/hep2g4.f")
    exe(id,workdir,
        "g77 pythia_main.f lcwrite.f hep2g4.f -L"+libdir+" -lpythia -o pythia.run")


def install_cmake(version,doit):

    # environment
    id="cmake-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("PATH",workdir+"/bin:${PATH}")
    if debugmode:
        set_environment("CMAKE","\"cmake -DCMAKE_BUILD_TYPE=Debug\"")
    else:
        set_environment("CMAKE","cmake")
    if not doit: return

    # get code
    wget(id,tardir,"http://www.cmake.org/files/v2.4/cmake-"+version
         +".tar.gz")
    exe(id,ilcbasedir,"rm -rf cmake-"+version)
    exe(id,ilcbasedir,"tar zxf "+tardir+"/cmake-"+version+".tar.gz")

    # build
    exe(id,workdir,"./configure --prefix="+workdir)
    exe(id,workdir,"make")
    exe(id,workdir,"make install")

    
def install_maven(version,doit):

    # environment
    id="maven-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("MAVEN_HOME",workdir)
    set_environment("PATH",workdir+"/bin:${PATH}")

    if doit:
        # get code (different naming schemes for 1.x and 2.x)
        if version[0]=="1":
            wget(id,tardir,
                 "http://archive.apache.org/dist/maven/binaries/maven-"\
                 +version+".tar.gz")
            exe(id,ilcbasedir,"tar zxf "+tardir+"/maven-"+version+".tar.gz")
            exe(id,workdir,"${MAVEN_HOME}/bin/install_repo.sh "\
                +workdir+"/repository")
        else:
            wget(id,tardir,
                 "http://archive.apache.org/dist/maven/binaries/maven-"\
                 +version+"-bin.tar.gz","maven-"+version+".tar.gz")
            exe(id,ilcbasedir,"tar zxf "+tardir+"/maven-"+version+".tar.gz")


    # this needs to be done even when not installing, but it always
    # needs to be done *after* the actual installation
    if version[0]=="1":
        # proxy and repository setup for maven1
        command_line="maven -Dmaven.home.local="+workdir
        if proxy_host!="":
            set_environment("MVN","\""+command_line\
                            +" -Dmaven.proxy.host="+proxy_host\
                            +" -Dmaven.proxy.port="+proxy_port+"\"")
        else:
            set_environment("MVN","\""+command_line+"\"")
    else:
        # set up repository location and proxy setting for maven2
        if os.path.exists(workdir):
            conf=open(workdir+"/conf/config.xml","w")
            conf.write("<settings>\n")
            conf.write("  <localRepository>\n")
            conf.write("    "+workdir+"/repository\n")
            conf.write("  </localRepository>\n")
            if proxy_host!="":
                conf.write("  <proxies>\n")
                conf.write("   <proxy>\n")
                conf.write("      <active>true</active>\n")
                conf.write("      <protocol>http</protocol>\n")
                conf.write("      <host>"+proxy_host+"</host>\n")
                conf.write("      <port>"+proxy_port+"</port>\n")
                conf.write("    </proxy>\n")
                conf.write("  </proxies>\n")
            conf.write("</settings>\n")
            conf.close()
            set_environment("MVN","\"mvn -s "+workdir+"/conf/config.xml\"")



    
def install_ccvssh(version,doit):

    # requirements:
    # - install
    # - make
    # - gcc
    # - gawk
    # - openssl

    # environment
    id="ccvssh-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("DESY_CCVSSH",workdir+"/bin/ccvssh")
    if not doit: return

    # get code
    wget(id,tardir,"http://www-zeuthen.desy.de/linear_collider/sources/ccvssh-"\
         +version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/ccvssh-"+version+".tgz")

    # build
    exe(id,workdir,"./configure --prefix="+workdir)
    exe(id,workdir,"make")
    exe(id,workdir,"make install")

    
def install_clhep(version,doit):

    # requirements:
    # - make
    # - install
    # - gawk
    # - g++
    # - ranlib
    
    # environment variables
    workdir=ilcbasedir+"/clhep-"+version
    set_environment("CLHEP_BASE_DIR",workdir)
    set_environment("CLHEP",workdir)
    set_environment("LD_LIBRARY_PATH","${LD_LIBRARY_PATH}:${CLHEP}/lib")
    if not doit: return
    
    # get code
    id="clhep-"+version
    #wget(id,tardir,"http://proj-clhep.web.cern.ch/proj-clhep/DISTRIBUTION/"\
    #     +"distributions/clhep-"+version+".tgz")
    wget(id,tardir,"http://proj-clhep.web.cern.ch/proj-clhep/DISTRIBUTION/"\
         +"distributions/clhep-"+version+"-src.tgz","clhep-"+version+".tgz")
    exe(id,workdir,"tar zxf "+tardir+"/clhep-"+version+".tgz")
    builddir=workdir+"/"+version+"/CLHEP"
    exe(id,builddir,"./configure --prefix="+workdir)
    exe(id,builddir,"make "+makeopts)
    exe(id,builddir,"make install")


def install_jaida(version,doit):

    # requirements:
    # - jdk
    # - svn

    # set up environment
    id="jaida-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("JAIDA_HOME",workdir)
    set_environment("LD_LIBRARY_PATH","${LD_LIBRARY_PATH}:"\
                    +workdir+"/lib/i386-"+arch)

    if doit:

        # get code
        wget(id,tardir,"ftp://ftp.slac.stanford.edu/software/freehep/JAIDA/v"
             +version+"/jaida-"+version+"-i386-"+arch+".tar.gz",
             "jaidalib-"+version+".tgz")
        wget(id,tardir,"ftp://ftp.slac.stanford.edu/software/freehep/JAIDA/v"
             +version+"/jaida-"+version+"-bin.tar.gz",
             "jaidabin-"+version+".tgz")
        exe(id,ilcbasedir,"tar zxf "+tardir+"/jaidabin-"+version+".tgz")
        exe(id,ilcbasedir,"tar zxf "+tardir+"/jaidalib-"+version+".tgz")

    if os.path.exists(workdir+"/lib"):
        classpath=""
        for filename in os.listdir(workdir+"/lib"):
            if filename[-4:]==".jar":
                if classpath!="": classpath+=":"
                classpath+=workdir+"/lib/"+filename
        set_environment("CLASSPATH",classpath+":${CLASSPATH}")


def install_aidajni_source(version,doit):

    # set up environment
    id="aidajni-"+version
    workdir=ilcbasedir+"/"+id
    tempdir=workdir+"_temp"
    tempdir1=tempdir+"/freehep-aidajni-"+version
    tempdir2=tempdir+"/aidaconfig-"+version
    #tempdir3=tempdir+"/aidajni-"+version
    set_environment("AIDAJNI_VERSION",version)
    set_environment("AIDAJNI_HOME",workdir)
    set_environment("AIDAJNI_NAME","freehep-aidajni-"+version)
    set_environment("CLASSPATH",
                    "${AIDAJNI_HOME}/lib/${AIDAJNI_NAME}.jar:${CLASSPATH}")
    set_environment("AIDAJNI_AOL","i386-"+arch)

    if not doit: return

    # get code
    exe(id,tempdir,"svn checkout svn://svn.freehep.org/svn/freehep/tags/freehep-aidajni-"+version+" freehep-aidajni-"+version)
    exe(id,tempdir,"svn checkout svn://svn.freehep.org/svn/freehep/tags/aida-config-"+version+" aidaconfig-"+version)
    #exe(id,tempdir,"svn checkout svn://svn.freehep.org/svn/freehep/tags/aidajni-"+version+" aidajni-"+version)

    # patch pom.xml to create shared library in addition to static library
    exe(id,tempdir1,"mv pom.xml pom.xml.orig")
    exe(id,tempdir1,"sed -e \"s|<libraries>|<libraries><library><type>shared</type></library>|g\" pom.xml.orig > pom.xml")

    # create a distribution package
    exe(id,tempdir1,"${MVN}")
    exe(id,tempdir2,"${MVN}")
    #exe(id,tempdir3,"${MVN} site:site")
    #exe(id,tempdir3,"${MVN}")
    #exe(id,tempdir3,"mv target/"+id+"${AIDAJNI_AOL}.tar.gz "+tardir+"/"+id+".tgz")

    # move everything to proper place
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,workdir,"mv "+tempdir2+"/target/nar/bin .")
    exe(id,workdir,"mv "+tempdir1+"/target/nar/include .")
    exe(id,workdir,"mv "+tempdir1+"/target/nar/javah-include .")
    exe(id,workdir,"mv "+tempdir1+"/target/nar/lib .")
    exe(id,workdir,"mv "+tempdir1+"/target/*.jar ./lib/")
    libdir=workdir+"/lib"
    exe(id,libdir,"ln -s ${AIDAJNI_NAME}.jar freehep-aidajni.jar")
    exe(id,libdir,"ln -s ${AIDAJNI_AOL}/static/lib${AIDAJNI_NAME}.a ./libAIDAJNI.a")
    exe(id,libdir,"ln -s ${AIDAJNI_AOL}/static/lib${AIDAJNI_NAME}.a ./libFHJNI.a")
    exe(id,libdir,"ln -s ${AIDAJNI_AOL}/shared/lib${AIDAJNI_NAME}.so ./libAIDAJNI.so")
    exe(id,libdir,"ln -s ${AIDAJNI_AOL}/shared/lib${AIDAJNI_NAME}.so ./libFHJNI.so")

    # install distribution package
    #exe(id,ilcbasedir,"tar zxf "+tardir+"/"+id+".tgz")
    exe(id,ilcbasedir,"rm -rf "+tempdir)


def install_aidajni(version,doit):

    # set up environment
    id="aidajni-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("AIDAJNI_VERSION",version)
    set_environment("AIDAJNI_HOME",workdir)
    set_environment("AIDAJNI_NAME","freehep-aidajni-"+version)
    set_environment("CLASSPATH",
                    "${AIDAJNI_HOME}/lib/${AIDAJNI_NAME}.jar:${CLASSPATH}")
    set_environment("AIDAJNI_AOL","i386-"+arch)

    if not doit: return

    # get code
    wget(id,tardir,"ftp://ftp.slac.stanford.edu/software/freehep/AIDAJNI/v"+version+"/aidajni-"+version+"-i386-"+arch+".tar.gz",id+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/"+id+".tgz")


def install_lcio(version,doit):

    # requirements:
    # - clhep
    # - jdk
    # - g++
    # - jaida?
    
    # set up environment
    workdir=ilcbasedir+"/lcio-"+version
    set_environment("LCIO",workdir)
    set_environment("LCIO_HOME",workdir)
    set_environment("PATH","${PATH}:"+workdir+"/bin")
    set_environment("LD_LIBRARY_PATH","${LD_LIBRARY_PATH}:"+workdir+"/lib")
    if python_bindings:
        set_environment("PYTHONPATH",workdir+"/src/python:${PYTHONPATH}")
    if not doit: return

    # get code
    set_environment("CVSROOT",":pserver:anonymous@cvs.freehep.org:/cvs/lcio",0)
    id="lcio-"+version
    exe(id,ilcbasedir,"cvs co -d "+workdir.split("/")[-1]\
        +" -r "+version+" lcio")

    # build
    exe(id,workdir,"${CMAKE} .")
    exe(id,workdir,"make install -f Makefile")

    #build python bindings
    if python_bindings:
        lciopy = workdir+"/src/python"
        #get fixed swig code
        exe(id,lciopy,"rm -rf lcio_swig.i")
        wget(id,lciopy,"http://www-pnp.physics.ox.ac.uk/~jeffery/lcioswig/"+version+"/lcio_swig.i")
        exe(id,lciopy,"make")

def install_root(version,doit):

    # set up environment
    workdir=ilcbasedir+"/root-"+version
    set_environment("ROOTSYS",workdir)
    set_environment("PATH","${PATH}:"+workdir+"/bin")
    set_environment("LD_LIBRARY_PATH","${LD_LIBRARY_PATH}:${ROOTSYS}/lib")
    if python_bindings:
         set_environment("PYTHONPATH","${PYTHONPATH}:${ROOTSYS}/pyroot:${ROOTSYS}/lib")
    if not doit: return
    
    # get code
    id="root-"+version
    wget(id,tardir,"ftp://root.cern.ch/root/root_"+version+".source.tar.gz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/root_"+version+".source.tar.gz")
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv root "+workdir)
    
    # build
    if python_bindings:
        #get python directory
        try:
            pyversion = install["python"][-1]
        except KeyError:
            pyversion = skip["python"][-1]
        pydir = ilcbasedir + "/python-"+pyversion
        exe(id,workdir,"./configure --enable-python --with-python-incdir="+pydir+"/include"+
        " --with-python-libdir="+pydir+
        " --enable-roofit --disable-cern")
    else:
        exe(id,workdir,"./configure --enable-roofit --disable-cern")
    exe(id,workdir,"gmake "+makeopts)
    exe(id,workdir,"gmake cintdlls "+makeopts)
    exe(id,workdir,"gmake install")


def install_raida(version,doit):

    # set up environment
    workdir=ilcbasedir+"/raida-"+version
    set_environment("RAIDA_HOME",workdir)
    set_environment("LD_LIBRARY_PATH","${LD_LIBRARY_PATH}:${RAIDA_HOME}/lib")
    #set_environment("PATH","${PATH}:"+workdir+"/bin")
    if not doit: return

    # get code
    set_environment("CVS_RSH","${DESY_CCVSSH}",0)
    set_environment("CVSROOT",":ext:anonymous:@cvssrv.ifh.de:/ilctools",0)
    id="raida-"+version
    exe(id,workdir,"${DESY_CCVSSH} login")
    set_environment("CVSROOT",":ext:anonymous@cvssrv.ifh.de:/ilctools",0)
    exe(id,ilcbasedir,"cvs co -d "+workdir.split("/")[-1]\
        +" -r "+version+" RAIDA")

    # remove relative path name from makefile (caused problems on OS X)
    #srcdir=workdir+"/src"
    #exe(id,srcdir,"mv GNUmakefile GNUmakefile.orig")
    #exe(id,srcdir,"sed -e 's|BASEDIR = ..|BASEDIR = "+workdir+"|g' "\
    #    +"GNUmakefile.orig > GNUmakefile")

    # compile and link
    exe(id,workdir,"${CMAKE} -DCMAKE_MODULE_PATH=${CMAKE_MODULE_PATH}"\
        +" -DROOT_HOME=${ROOTSYS}")
    exe(id,workdir,"make install "+makeopts)


def install_gear(version,doit):

    # set up environment
    workdir=ilcbasedir+"/gear-"+version
    set_environment("GEAR",workdir)
    set_environment("LD_LIBRARY_PATH","${LD_LIBRARY_PATH}:"+workdir+"/lib")
    set_environment("GEARVERSION",version)
    set_environment("GEAR_USE_AIDA","1")
    if not doit: return

    # get code
    id="gear-"+version
    wget(id,tardir,"http://www-zeuthen.desy.de/lc-cgi-bin/cvsweb.cgi/gear/"\
         +"gear.tar.gz?cvsroot=gear;only_with_tag="+version+";tarball=1",\
         "gear_"+version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/gear_"+version+".tgz")
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv gear "+workdir)

    # build (corresponding to env.sh script in gear directory)
    exe(id,workdir,"${CMAKE} .")
    exe(id,workdir,"make install -f Makefile")


def install_geant(version,doit):

    # set up environment
    workdir=ilcbasedir+"/geant"+version
    set_environment("G4INSTALL",workdir)
    set_environment("G4WORKDIR",workdir)
    set_environment("G4SYSTEM",arch)
    set_environment("G4LIB_USE_GRANULAR","1")
    set_environment("G4LEVELGAMMADATA",workdir+"/data/PhotonEvaporation2.0")
    set_environment("G4VIS_BUILD_OPENGLX_DRIVER","1")
    set_environment("G4VIS_USE_OPENGLX","1")
    #set_environment("G4VIS_BUILD_OPENGLWIN32_DRIVER","1")
    #set_environment("G4VIS_USE_OPENGLWIN32","1")
    set_environment("G4VIS_BUILD_OPENGLXM_DRIVER","1")
    set_environment("G4VIS_USE_OPENGLXM","1")
    set_environment("G4VIS_BUILD_RAYTRACERX_DRIVER","1")
    set_environment("G4VIS_USE_RAYTRACERX","1")
    #set_environment("G4UI_BUILD_XM_SESSION","1")
    #set_environment("G4UI_USE_XM","1")
    set_environment("G4UI_USE_TCSH","1")
    if debugmode:
        set_environment("G4DEBUG","1")
    if not doit: return

    # get code
    id="geant"+version
    wget(id,tardir,
    "http://geant4.web.cern.ch/geant4/support/source/geant"+version+".gtar.gz")
    wget(id,tardir,
         "http://geant4.cern.ch/support/source/PhotonEvaporation.2.0.tar.gz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/geant"+version+".gtar.gz")
    exe(id,workdir,"mkdir -p data")
    exe(id,workdir+"/data","tar zxf "+tardir+"/PhotonEvaporation.2.0.tar.gz")
    exe(id,workdir+"/source","gmake "+makeopts)

    # build physics list libraries for versions before 4.8.2
    if os.path.isdir(workdir+"/physics_lists/hadronic"):
        exe(id,workdir+"/physics_lists/hadronic","gmake "+makeopts)


def install_mokka(version,doit):

    # set up environment
    workdir=ilcbasedir+"/mokka-"+version
    set_environment("G4WORKDIR",workdir)
    set_environment("PATH","${PATH}:"+workdir+"/bin/${G4SYSTEM}")
    if not doit: return

    # get code
    id="mokka-"+version
    set_environment("CVSROOT",
                    ":pserver:anoncvs:%ilc%@pollin1.in2p3.fr:/home/flc/cvs",0)
    exe(id,ilcbasedir,"cvs co -r %s Mokka"%version)
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv Mokka "+workdir)

    # now compile and link
    exe(id,workdir+"/source","gmake "+makeopts)
    

def install_gsl(version,doit):

    # set up environment
    workdir=ilcbasedir+"/gsl-"+version
    set_environment("GSL_HOME",workdir)
    set_environment("LD_LIBRARY_PATH","${LD_LIBRARY_PATH}:${GSL_HOME}/lib")
    if not doit: return

    # get code
    id="gsl-"+version
    wget(id,tardir,"ftp://ftp.gnu.org/gnu/gsl/gsl-"+version+".tar.gz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/gsl-"+version+".tar.gz")

    # build
    exe(id,workdir,"./configure --prefix="+workdir)
    exe(id,workdir,"make "+makeopts)
    exe(id,workdir,"make install")
  
    # why are many files world-writeable here?!?
    exe(id,ilcbasedir,"chmod -R go-w "+workdir)


def install_heppdt(version,doit):

    # set up environment
    workdir=ilcbasedir+"/heppdt-"+version
    set_environment("HEPPDT",workdir)
    set_environment("LD_LIBRARY_PATH","${LD_LIBRARY_PATH}:"+workdir+"/lib")
    if not doit: return

    # get code
    id="heppdt-"+version
    wget(id,tardir,"http://lcgapp.cern.ch/project/simu/HepPDT/download/HepPDT-"\
         +version+".tar.gz")
    exe(id,workdir,"tar zxf "+tardir+"/HepPDT-"+version+".tar.gz")

    # build code
    builddir=workdir+"/HepPDT-"+version
    exe(id,builddir,"./configure --prefix="+workdir)
    exe(id,builddir,"make "+makeopts)
    exe(id,builddir,"make install")

    # make code appear in CLHEP directory to be compatible with older versions
    #clhep=eval("${CLHEP}")
    #exe(id,clhep+"/include/CLHEP","ln -sf "+workdir+"/include/HepPDT .")
    #exe(id,clhep+"/include/CLHEP","ln -sf "+workdir+"/include/HepPID .")
    #exe(id,clhep+"/include","ln -sf "+workdir+"/include/HepPDT .")
    #exe(id,clhep+"/include","ln -sf "+workdir+"/include/HepPID .")
    #exe(id,clhep+"/lib","ln -sf "+workdir+"/lib/libHepPDT.a .")
    #exe(id,clhep+"/lib","ln -sf "+workdir+"/lib/libHepPDT.so .")
    #exe(id,clhep+"/lib","ln -sf "+workdir+"/lib/libHepPID.a .")
    #exe(id,clhep+"/lib","ln -sf "+workdir+"/lib/libHepPID.so .")


def install_marlin(version,doit):

    # requirements
    # - qt4 (for GUI)
    
    # set up environment
    workdir=ilcbasedir+"/marlin-"+version
    set_environment("MARLIN",workdir)
    set_environment("MARLIN_USE_AIDA","1")
    if debugmode:
        set_environment("MARLINDEBUG","1")
    set_environment("PATH","${PATH}:"+workdir+"/bin")
    if not doit: return

    # get code
    id="marlin-"+version
    wget(id,tardir,"http://www-zeuthen.desy.de/lc-cgi-bin/cvsweb.cgi/"\
         +"Marlin/Marlin.tar.gz?cvsroot=marlin;only_with_tag="+version\
         +";tarball=1","Marlin_"+version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/Marlin_"+version+".tgz")
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv Marlin "+workdir)

    # patch processorloader not to unload dynamic libraries at end of program.
    # deferring this unload to the operating system allows valgrind to analyze
    # symbol tables of dynamic libraries even after Marlin shuts down.
    patchdir=workdir+"/src"
    exe(id,patchdir,"mv ProcessorLoader.cc ProcessorLoader.cc.orig")
    exe(id,patchdir,"sed -e \"s|dlclose|//dlclose|g\" "\
        +"ProcessorLoader.cc.orig > ProcessorLoader.cc")
    
    # build
    if USE_RAIDA:
        exe(id,workdir,"${CMAKE} -DCMAKE_MODULE_PATH=${CMAKE_MODULE_PATH}"\
            +" -DBUILD_WITH=\"RAIDA CLHEP GEAR\" -DLCIO_HOME=${LCIO_HOME}"\
            +" -DGEAR_HOME=${GEAR} -DRAIDA_HOME=${RAIDA_HOME}"\
            +" -DCLHEP_HOME=${CLHEP}")
    else:
        exe(id,workdir,"${CMAKE} -DCMAKE_MODULE_PATH=${CMAKE_MODULE_PATH}"\
            +" -DBUILD_WITH=\"AIDAJNI CLHEP GEAR\" -DLCIO_HOME=${LCIO_HOME}"\
            +" -DGEAR_HOME=${GEAR} -DAIDAJNI_HOME=${AIDAJNI_HOME}"\
            +" -DCLHEP_HOME=${CLHEP}")
    exe(id,workdir,"gmake install -f Makefile "+makeopts)


def install_marlinutil(version,doit):

    # requires gsl

    workdir=ilcbasedir+"/marlinutil-"+version
    set_environment("MARLINUTIL",workdir)
    set_environment("PATH","${PATH}:"+workdir+"/bin")
    if not doit:return

    # get code
    id="marlinutil-"+version
    wget(id,tardir,"http://www-zeuthen.desy.de/lc-cgi-bin/cvsweb.cgi/"\
         +"MarlinUtil/MarlinUtil.tar.gz?cvsroot=marlinreco;only_with_tag="\
         +version+";tarball=1","MarlinUtil_"+version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/MarlinUtil_"+version+".tgz")
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv MarlinUtil "+workdir)

    # build
    exe(id,workdir,"${CMAKE} -DCMAKE_MODULE_PATH=${CMAKE_MODULE_PATH}"\
        +" -DMarlin_HOME=${MARLIN} -DGEAR_HOME=${GEAR}"\
        +" -DLCIO_HOME=${LCIO}"\
        +" -DCLHEP_HOME=${CLHEP} -DGSL_HOME=${GSL_HOME}")
    exe(id,workdir,"make install -f Makefile "+makeopts)


def install_boost(version,doit):

    workdir=ilcbasedir+"/boost-"+version
    set_environment("BOOSTINC",workdir)
    if not doit: return

    # get code
    id="boost-"+version
    wget(id,tardir,
         "http://downloads.sourceforge.net/boost/boost_"+version+".tar.gz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/boost_"+version+".tar.gz")
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv boost_"+version+" "+workdir)

    # build
    exe(id,workdir,"./configure --prefix="+workdir)
    exe(id,workdir,"make "+makeopts)
    exe(id,workdir,"make install")


def install_lapack(version,doit):

    # set up environment
    workdir=ilcbasedir+"/lapack-"+version
    set_environment("LAPACK",workdir)
    if not doit: return

    # get code
    wget(id,tardir,"http://www.netlib.org/lapack/lapack-"+version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/lapack-"+version+".tgz")

    # build
    exe(id,workdir,"cp -p make.inc.example make.inc")
    exe(id,workdir,"make blaslib")
    exe(id,workdir,"make")


def install_cernlib(version,doit):

    # requires lapack, heppdt
    
    # set up environment
    workdir=ilcbasedir+"/cernlib-"+version
    set_environment("CERN",ilcbasedir)
    set_environment("CERN_LEVEL","cernlib-"+version)
    set_environment("CERN_ROOT",workdir)
    set_environment("CVSCOSRC",workdir+"/src")
    set_environment("PATH","${PATH}:"+workdir+"/bin")
    if not doit: return

    # get code
    id="cernlib-"+version
    wget(id,tardir,"http://cernlib.web.cern.ch/cernlib/download/"+version\
         +"_source/tar/"+version+"_src.tar.gz","cernlib_src_"+version+".tgz")
    wget(id,tardir,"http://cernlib.web.cern.ch/cernlib/download/"+version\
         +"_source/tar/include.tar.gz","cernlib_include_"+version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/cernlib_src_"+version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/cernlib_include_"+version+".tgz")
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv "+version+" "+workdir)

    # clean up potential leftovers that repeated builds cannot deal with
    #exe(id,workdir+"/lib","rm -f xsneut95.dat")

    # build
    builddir=workdir+"/build"
    #exe(id,builddir,"${CVSCOSRC}/config/imake_boot")
    #exe(id,builddir,"gmake bin/kuipc "+makeopts)
    #exe(id,builddir,"gmake scripts/Makefile "+makeopts)
    #exe(id,builddir+"/scripts","gmake install.bin")
    #exe(id,builddir,"gmake packlib/Makefile "+makeopts)
    #exe(id,builddir+"/packlib","gmake install.lib")
    #exe(id,builddir,"gmake mathlib/Makefile "+makeopts)
    #exe(id,builddir+"/mathlib","gmake install.lib")
    exe(id,builddir,"${CVSCOSRC}/config/imake_boot")
    exe(id,builddir,"gmake bin/kuipc")
    exe(id,builddir,"gmake scripts/Makefile")
    exe(id,builddir+"/scripts","gmake install.bin")
    exe(id,builddir,"gmake")
    exe(id,workdir+"/lib","ln -s ${LAPACK}/lapack_LINUX.a liblapack3.a")
    exe(id,workdir+"/lib","ln -s ${LAPACK}/blas_LINUX.a  libblas.a")
    exe(id,builddir+"/pawlib","gmake install.bin")
    exe(id,builddir+"/packlib","gmake install.bin")


def install_marlinreco(version,doit):

    # requires marlinutil, cernlib
    
    id="marlinreco-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("MARLINRECO",workdir)
    set_environment("MARLIN_DLL","${MARLIN_DLL}:"\
                    +workdir+"/lib/libMarlinReco.so")
    if not doit: return

    # get code
    wget(id,tardir,"http://www-zeuthen.desy.de/lc-cgi-bin/cvsweb.cgi/"\
         +"MarlinReco/MarlinReco.tar.gz?cvsroot=marlinreco;only_with_tag="\
         +version+";tarball=1","MarlinReco_"+version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/MarlinReco_"+version+".tgz")
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv MarlinReco "+workdir)

    # build
    #set_environment("MARLINWORKDIR","${MARLIN}")
    exe(id,workdir,"${CMAKE} -DCMAKE_MODULE_PATH=${CMAKE_MODULE_PATH}"\
        +" -DMarlin_HOME=${MARLIN} -DMarlinUtil_HOME=${MARLINUTIL}"\
        +" -DGEAR_HOME=${GEAR} -DLCIO_HOME=${LCIO} -DCLHEP_HOME=${CLHEP}"\
        +" -DGSL_HOME=${GSL_HOME} -DCERNLIB_HOME=${CERN_ROOT}");
    exe(id,workdir,"make install -f Makefile")


def install_sidigi(version,doit):

    id="sidigi-"+version
    workdir=ilcbasedir+"/"+id
    if not doit: return

    # get code
    wget(id,tardir,"http://www-zeuthen.desy.de/lc-cgi-bin/cvsweb.cgi/"\
         +"SiliconDigi/SiliconDigi.tar.gz?cvsroot=marlinreco;only_with_tag="\
         +version+";tarball=1","SiliconDigi_"+version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/SiliconDigi_"+version+".tgz")
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv SiliconDigi "+workdir)

    # build
    #exe(id,workdir,"${CMAKE} -DCMAKE_MODULE_PATH=${CMAKE_MODULE_PATH}"\
    #    +" -DMarlin_HOME=${MARLIN} -DMarlinUtil_HOME=${MARLINUTIL}"\
    #    +" -DGEAR_HOME=${GEAR} -DLCIO_HOME=${LCIO} -DCLHEP_HOME=${CLHEP}"\
    #    +" -DGSL_HOME=${GSL_HOME} -DCERNLIB_HOME=${CERN_ROOT}");
    #exe(id,workdir,"make install -f Makefile")


def install_ced(version,doit):

    workdir=ilcbasedir+"/ced-"+version
    set_environment("PATH","${PATH}:"+workdir)
    if not doit: return
    
    # get code
    id="ced-"+version
    wget(id,tardir,"http://www-zeuthen.desy.de/lc-cgi-bin/cvsweb.cgi/CED/"\
         +"CED.tar.gz?cvsroot=marlinreco;only_with_tag="+version+";tarball=1",\
         "CED_"+version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+ilcbasedir+"/tarfiles/CED_"+version+".tgz")
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv CED "+workdir)
    
    # build
    exe(id,workdir,"make "+makeopts)


def install_lcfivertex(version,doit):

    id="lcfivertex-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("PATH","${PATH}:"+workdir+"/bin")
    set_environment("MARLIN_DLL","${MARLIN_DLL}:"\
                    +workdir+"/lib/libLCFIVertex.so")
    # many plots in AIDA -> need more memory for JVM
    set_environment("JVM_ARGS","-Xmx"+str(java_size)+"m")
    if not doit: return

    # get code
    wget(id,tardir,
         "http://www-zeuthen.desy.de/lc-cgi-bin/cvsweb.cgi/LCFIVertex/"\
         +"LCFIVertex.tar.gz?cvsroot=marlinreco;only_with_tag="+version\
         +";tarball=1","lcfivertex-"+version+".tgz")
    exe(id,ilcbasedir,"rm -rf lcfivertex-"+version)
    exe(id,ilcbasedir,"tar zxf "+tardir+"/lcfivertex-"+version+".tgz")
    exe(id,ilcbasedir,"mv LCFIVertex lcfivertex-"+version)

    # temporary: get rid of LCFIAIDA plot when in RAIDA mode
    if USE_RAIDA:
        exe(id,workdir,"rm src/LCFIAIDAPlotProcessor.cc include/LCFIAIDAPlotProcessor.h")

    # hopefully temporary: cmake expects boost library in local subdir,
    # so let's create a link from there to our actual boost installation
    exe(id,workdir,"ln -sf ${BOOSTINC} ./boost")

    # build
    if USE_RAIDA:
        exe(id,workdir,"${CMAKE} -DCMAKE_MODULE_PATH=${CMAKE_MODULE_PATH}"\
            +" -DMarlin_HOME=${MARLIN} -DLCIO_HOME=${LCIO}"\
            +" -DBUILD_WITH=\"ROOT;RAIDA;GEAR\" -DROOT_HOME=${ROOTSYS}"\
            +" -DRAIDA_HOME=${RAIDA_HOME}"\
            +" -DGEAR_HOME=${GEAR}"\
            +" -DCMAKE_CXX_FLAGS:STRING=\"-DUSEROOT\"")
    else:
        exe(id,workdir,"${CMAKE} -DCMAKE_MODULE_PATH=${CMAKE_MODULE_PATH}"\
            +" -DMarlin_HOME=${MARLIN} -DLCIO_HOME=${LCIO}"\
            +" -DBUILD_WITH=\"ROOT;AIDAJNI;GEAR\" -DROOT_HOME=${ROOTSYS}"\
            +" -DAIDAJNI_HOME=${AIDAJNI_HOME}"\
            +" -DGEAR_HOME=${GEAR}"\
            +" -DCMAKE_CXX_FLAGS:STRING=\"-DUSEROOT\"")
    exe(id,workdir,"make install -f Makefile")
    exe(id,workdir+"/doc","doxygen")


def install_pandorapfa(version,doit):

    id="pandorapfa-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("MARLIN_DLL","${MARLIN_DLL}:"\
                    +workdir+"/lib/libPandoraPFA.so")
    if not doit: return

    # get code
    id="pandorapfa-"+version
    wget(id,tardir,"http://www-zeuthen.desy.de/lc-cgi-bin/cvsweb.cgi/"\
         +"PandoraPFA/PandoraPFA.tar.gz?cvsroot=marlinreco;only_with_tag="\
         +version+";tarball=1","pandorapfa_"+version+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/pandorapfa_"+version+".tgz")
    exe(id,ilcbasedir,"rm -rf "+workdir)
    exe(id,ilcbasedir,"mv PandoraPFA "+workdir)

    # build
    exe(id,workdir,"${CMAKE} -DCMAKE_MODULE_PATH=${CMAKE_MODULE_PATH} -DMarlin_HOME=${MARLIN} -DMarlinUtil_HOME=${MARLINUTIL} -DLCIO_HOME=${LCIO} -DGEAR_HOME=${GEAR} -DGSL_HOME=${GSL_HOME} -DROOT_HOME=${ROOTSYS}")
    exe(id,workdir,"make install -f Makefile "+makeopts)

def install_jas3(version,doit):

    id="jas3-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("PATH","${PATH}:"+workdir)
    set_environment("JVM_ARGS","-Xmx"+str(java_size)+"m")
    if proxy_host!="":
        set_environment("JASJVM_ARGS","\"-Dhttp.proxyHost="+proxy_host\
                        +" -Dhttp.proxyPort="+proxy_port+" -Xmx"\
                        +str(java_size)+"m\"")
    else:
        set_environment("JASJVM_ARGS","-Xmx"+str(java_size)+"m")
    if not doit: return
    
    # get code
    wget(id,tardir,"ftp://ftp.slac.stanford.edu/software/jas/JAS3/v"+version\
         +"/jas3-Linux-"+version+".tar.gz",id+".tgz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/"+id+".tgz")

def install_swig(vesion,doit):
    id="swig-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("PATH",workdir+"/bin:${PATH}")
    if not doit: return
    #get code
    exe(id,ilcbasedir,"rm -rf "+workdir)
    wget(id,tardir,"http://heanet.dl.sourceforge.net/sourceforge/swig/"+id+".tar.gz")
    exe(id,ilcbasedir,"tar zxf "+tardir+"/"+id+".tar.gz")

    # build
    exe(id,workdir,"./configure --prefix="+workdir)
    exe(id,workdir,"make "+makeopts)
    exe(id,workdir,"make install")

def install_python(version,doit):
    id="python-"+version
    workdir=ilcbasedir+"/"+id
    set_environment("PATH",workdir+"/bin:${PATH}")
    if not doit: return
    #get code
    exe(id,ilcbasedir,"rm -rf "+workdir)
    wget(id,tardir,"http://www.python.org/ftp/python/"+version+"/Python-"+version+".tar.bz2")
    exe(id,ilcbasedir,"tar jxf "+tardir+"/Python-"+version+".tar.bz2")
    exe(id,ilcbasedir,"mv Python-"+version+" python-"+version)
    
    # build
    exe(id,workdir,"./configure --prefix="+workdir)
    exe(id,workdir,"make "+makeopts)
    exe(id,workdir,"make install")
    
#####################
# general checks
######################

# check for gcc version 4
is_gcc4=len(os.popen("gcc --version|grep \"\\ 4\.\"").readlines())

# check for essential programs
exe("","","which make","ERROR: please install make")
exe("","","which g77","ERROR: please install g77")
if is_gcc4:
    exe("","","which gfortran","ERROR: please install gfortran")
exe("","","which g++","ERROR: please install g++")
exe("","","which javac","ERROR: please install Java Development Kit")
exe("","","which cvs","ERROR: please install CVS client")
exe("","","which mysql_config","ERROR: please install mysql headers")
exe("","","which doxygen","ERROR: please install doxygen")
exe("","","which wget","ERROR: please install wget")


######################
# general preparations
######################

exe("","","mkdir -p "+ilcbasedir,\
    "ERROR: need permission to create directory "+ilcbasedir)
exe("","","chown `whoami`:`id -gn` "+ilcbasedir,\
    "ERROR: need permission to change ownership of directory "+ilcbasedir)
exe("","","mkdir -p "+ilcbasedir+"/history",
    "ERROR: need write access to directory "+ilcbasedir)

# get network proxy configuration
if os.getenv("http_proxy"):
    proxy=os.getenv("http_proxy")
    proxy=proxy.replace("http://","")
    proxy=proxy.replace("http:","")
    print "\nHTTP PROXY:",proxy,"\n"
    if proxy.find(":")>0:
        proxy_host=proxy.split(":")[0]
        proxy_port=proxy.split(":")[1]
    else:
        proxy_host=proxy
        proxy_port="80"
else:
    proxy_host=""
    proxy_port=0
    print "\nNO HTTP PROXY CONFIGURED, using direct internet connection\n"

# try to analyze system to estimate optimal Java memory allocation
try:
    # get amount of memory available per processor
    result=os.popen("cat /proc/meminfo|grep -i memtotal").readlines()[0]
    memsize=int(result.split()[1])
    # get number of logical processors
    result=os.popen("cat /proc/cpuinfo|cut -c 1-9|grep -i processor").readlines()
    numcpu=len(result)
    print "number of logical CPUs:",numcpu
    print "total amount of memory:",memsize,"kb"
    java_size=int(memsize/numcpu/1024)
except:
    # fallback value if system analysis fails
    java_size=512
print "allocating",java_size,"MB to Java virtual machine\n"

timestamp=time.strftime("%Y%m%d_%H%M%S")
logfile=ilcbasedir+"/history/"+timestamp+".log"
exe("","","rm -f "+ilcbasedir+"/install.log")
exe("","","ln -s "+logfile+" "+ilcbasedir+"/install.log")
print "---> writing remaining installation log into "+logfile

exe("general",ilcbasedir,"rm -f "+setupfile+".sh")
exe("general",ilcbasedir,"rm -f "+setupfile+".csh")

# save original command and library paths so that user can switch between
# different ILC software work areas more easily
set_environment("PATH_SAVE","${PATH}")
set_environment("LD_LIBRARY_PATH_SAVE","${LD_LIBRARY_PATH}")
set_environment("PYTHONPATH_SAVE","${PYTHONPATH}")

# workaround for scientific linux and openSUSE: set JAVA_HOME properly
set_environment("JAVA_HOME","/etc/alternatives/java_sdk")

# copy this script into installation directory, for later reference
exe("general","","cp -p "+sys.argv[0]+" "+ilcbasedir+"/history/"
    +timestamp+".py")


######################
# installation loop
######################

for package in order:
    if install.has_key(package):
        # do full installation of this package
        doit=1
        versionlist=install[package]
    elif skip.has_key(package):
        # don't install this (but still need to set up environment variables)
        doit=0
        versionlist=skip[package]
    else:
        # user did not specify whether to install or skip this package!
        log("ERROR: install/skip not specified for package "+package)
        sys.exit(1)
    if len(versionlist)==0:
        # oops, we do need to have a specific version number to install!
        log("ERROR: no package version specified for package "+package)
        sys.exit(1)

    # loop over all requested version numbers
    for version in versionlist:
        if doit:
            log("installing package "+package+", version "+version)
        else:
            log("setting up package "+package+", version "+version)
        # call dedicated installation routine.
        try:
            locals()["install_"+package](version,doit)
        except KeyError:
            log("ERROR: no installation instructions for "+package)
            sys.exit(1)