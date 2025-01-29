import arcpy;
import sys,os;
import zipfile;
import json;
import getpass;
import datetime,re,difflib;
import util;

import importlib;
cd = importlib.import_module('util');
importlib.reload(cd);

###############################################################################
class Toolbox(object):

   def __init__(self):

      self.label = "StorageStagingSiteUtil";
      self.alias = "StorageStagingSiteUtil";

      self.tools = [];
      self.tools.append(AOISetup);
      self.tools.append(LoadNewAOI);
      self.tools.append(DeleteAOI);
      self.tools.append(RenameAOI);
      self.tools.append(ScenarioSetup);
      self.tools.append(LoadNewScenario);
      self.tools.append(DeleteScenario);
      self.tools.append(RenameScenario);
      self.tools.append(DuplicateScenario);
      self.tools.append(AddScenarioToMap);
      self.tools.append(RasterToResults);
      self.tools.append(PolygonToResults);

###############################################################################
class AOISetup(object):

   #...........................................................................
   def __init__(self):

      self.label              = "A1 AOI Setup";
      self.name               = "AOISetup";
      self.description        = "AOISetup";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):
   
      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
      
      cf = util.fetchConfig();

      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val = "Please save or delete all pending edits before proceeding.";
         err_enb = True;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "Purge Existing AOIs"
         ,name          = "PurgeExistingAOIs"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param1.value = False;

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "Load Sample AOIs"
         ,name          = "LoadSampleAOIs"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param2.value = True;

      ##---------------------------------------------------------------------##
      param3 = arcpy.Parameter(
          displayName   = "AOI Storage Location"
         ,name          = "AOIStorageLocation"
         ,datatype      = ["DEWorkspace","GPString"]
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param3.value = cf['aoistorage'];
      
      ##---------------------------------------------------------------------##
      param4 = arcpy.Parameter(
          displayName   = "AOI Storage Location_ref"
         ,name          = "AOIStorageLocation_ref"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = False
      );
      param4.value = cf['aoistorage'];

      params = [
          param0
         ,param1
         ,param2
         ,param3
         ,param4
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      workspace = arcpy.env.workspace;
      cf        = util.fetchConfig();

      ##---------------------------------------------------------------------##
      if parameters[1].valueAsText == "true":
         boo_purge = True;
      else:
         boo_purge = False;

      if parameters[2].valueAsText == "true":
         boo_load = True;
      else:
         boo_load = False;

      aoi_loc = parameters[3].valueAsText;
      aoi_ref = parameters[4].valueAsText;
      if aoi_loc == "" or aoi_loc == " ":
         aoi_loc = None;
         
      if aoi_ref == "" or aoi_ref == " ":
         aoi_ref = None;

      ##---------------------------------------------------------------------##
      if (aoi_loc is None and aoi_ref is None) or aoi_loc == aoi_ref:
         # Do nothing
         None;
         
      else:
         if aoi_loc is None and aoi_ref is not None:
            arcpy.AddMessage(".  Resetting aoistorage to default...");
            cf = util.updateConfig('aoistorage','default');
         
         else:
            arcpy.AddMessage(".  Adjusting configuration...");
            cf = util.updateConfig('aoistorage',aoi_loc);

      ##---------------------------------------------------------------------##
      if boo_purge:
         util.dzlog(".  Purge requested.",arcmsg=True);
         util.purgeFGDB(workspace);
         util.purgeFGDB(arcpy.env.scratchGDB);

         ##..................................................................##
         if arcpy.Exists(cf['aoistorage']):

            util.purgeFGDB(cf['aoistorage']);

      ##---------------------------------------------------------------------##
      if not arcpy.Exists(cf['aoistorage']):
         util.dzlog(".  Creating new AreaOfInterestStorage FGDB.",arcmsg=True);

         pf = os.path.split(cf['aoistorage']);
         arcpy.CreateFileGDB_management(
             out_folder_path = pf[0]
            ,out_name        = pf[1]
         );

      ##---------------------------------------------------------------------##
      if not arcpy.Exists(cf['aoistorage'] + os.sep + util.g_aoi_fc):

         util.dzlog(".  Creating AreaOfInterest feature class.",arcmsg=True);

         arcpy.env.workspace = cf['aoistorage'];
         arcpy.CreateFeatureclass_management(
             out_path          = cf['aoistorage']
            ,out_name          = util.g_aoi_fc
            ,geometry_type     = "POLYGON"
            ,has_m             = "DISABLED"
            ,has_z             = "DISABLED"
            ,spatial_reference = arcpy.SpatialReference(util.g_srid)
            ,config_keyword    = None
         );

         arcpy.management.AddFields(
             util.g_aoi_fc
            ,[
                ['aoi_id'                    ,'TEXT'    ,'Area of Interest ID'        ,255, None,'']
               ,['sloperaster'               ,'TEXT'    ,'Slope Raster'               ,255, None,'']
               ,['sloperastersource'         ,'TEXT'    ,'Slope Raster Source'        ,2000,None,'']
               ,['slopegridsize'             ,'DOUBLE'  ,'Slope Grid Size (m2)'       ,None,None,'']
               ,['landcoverraster'           ,'TEXT'    ,'Land Cover Raster'          ,255, None,'']
               ,['landcoverrastersource'     ,'TEXT'    ,'Land Cover Raster Source'   ,2000,None,'']
               ,['landcovergridsize'         ,'DOUBLE'  ,'Land Cover Grid Size (m2)'  ,None,None,'']
               ,['nhdfc'                     ,'TEXT'    ,'NHD Feature Class'          ,255, None,'']
               ,['nhdfcsource'               ,'TEXT'    ,'NHD Source'                 ,2000,None,'']
               ,['roadsfc'                   ,'TEXT'    ,'Roads Feature Class'        ,255, None,'']
               ,['roadsfcsource'             ,'TEXT'    ,'Roads Feature Class Source' ,2000,None,'']
               ,['ssurgofc'                  ,'TEXT'    ,'SSURGO Feature Class'       ,255, None,'']
               ,['ssurgofcsource'            ,'TEXT'    ,'SSURGO Feature Class Source',2000,None,'']
               ,['vectorbuffer'              ,'DOUBLE'  ,'Vector Buffer Amount (Km)'  ,None,None,'']
               ,['username'                  ,'TEXT'    ,'User Name'                  ,255, None,'']
               ,['datecreated'               ,'DATE'    ,'Date Created'               ,None,None,'']
               ,['notes'                     ,'TEXT'    ,'Notes'                      ,255, None,'']
             ]
         );

      ##---------------------------------------------------------------------##
      if boo_load:

         if 'sampledata' in cf:

            samples = cf['sampledata'];

            if len(samples) > 0:

               for item in samples:

                  sample = AOI(
                      sample_input=item
                     ,cf=cf
                  );
                  util.dzlog(".  Loading " + sample.aoi_id + " AOI ID.",arcmsg=True);
                  sample.unzipSample();
                  sample.loadSample();

###############################################################################
class LoadNewAOI(object):

   #...........................................................................
   def __init__(self):

      self.label              = "A2 Load New AOI";
      self.name               = "LoadNewAOI";
      self.description        = "LoadNewAOI";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
         
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
         
      #########################################################################
      stash = util.read_stash(aprx=aprx);
      if 'sloperaster' in stash:
         sloperaster = stash['sloperaster'];
      else:
         sloperaster = None;
         
      if 'landcoverraster' in stash:
         landcoverraster = stash['landcoverraster'];
      else:
         landcoverraster = None;
         
      if 'nhdfc' in stash:
         nhdfc = stash['nhdfc'];
      else:
         nhdfc = None;
         
      if 'roadsfc' in stash:
         roadsfc = stash['roadsfc'];
      else:
         roadsfc = None;

      if 'ssurgofc' in stash:
         ssurgofc = stash['ssurgofc'];
      else:
         ssurgofc = None;     
      
      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val = "Please save or delete all pending edits before proceeding.";
         err_enb = True;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "AOI ID"
         ,name          = "AOIID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "AOI Polygon"
         ,name          = "AOIPolygon"
         ,datatype      = "GPFeatureRecordSetLayer"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param2.filter.list = ["Polygon"];
      
      ##---------------------------------------------------------------------##
      param3 = arcpy.Parameter(
          displayName   = "AOI Polygon Bypass"
         ,name          = "AOIPolygonBypass"
         ,datatype      = "DEFeatureClass"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = False
      );
      
      ##---------------------------------------------------------------------##
      param4 = arcpy.Parameter(
          displayName   = "Storage-Siting-Staging ED Index File"
         ,name          = "SSSEDIndexFile"
         ,datatype      = "DEFile"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param4.filter.list = ['json'];

      ##---------------------------------------------------------------------##
      param5 = arcpy.Parameter(
          displayName   = "National Elevation Dataset (NED) Slope Raster"
         ,name          = "NEDSlopeRaster"
         ,datatype      = "DERasterDataset"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param5.value = sloperaster;

      ##---------------------------------------------------------------------##
      param6 = arcpy.Parameter(
          displayName   = "National Land Cover (NLCD) Raster"
         ,name          = "NationalLandCoverRaster"
         ,datatype      = "DERasterDataset"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param6.value = landcoverraster;

      ##---------------------------------------------------------------------##
      param7 = arcpy.Parameter(
          displayName   = "National Hydrography Dataset (NHD)"
         ,name          = "NationalHydrographyDataset"
         ,datatype      = "DEFeatureClass"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param7.value = nhdfc;

      ##---------------------------------------------------------------------##
      param8 = arcpy.Parameter(
          displayName   = "The National Map (TNM) Transportation Dataset"
         ,name          = "TNMRoads"
         ,datatype      = "DEFeatureClass"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param8.value = roadsfc;

      ##---------------------------------------------------------------------##
      param9 = arcpy.Parameter(
          displayName   = "Esri Soil Survey Geographic Database (SSURGO)"
         ,name          = "EsriSSURGO"
         ,datatype      = "DEFeatureClass"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param9.value = ssurgofc;
      
      ##---------------------------------------------------------------------##
      param10 = arcpy.Parameter(
          displayName   = "Vector Buffer (Km)"
         ,name          = "VectorBuffer"
         ,datatype      = "GPDouble"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param10.value = 5;

      ##---------------------------------------------------------------------##
      param11 = arcpy.Parameter(
          displayName   = "Optional Notes"
         ,name          = "OptionalNotes"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );

      params = [
          param0
         ,param1
         ,param2
         ,param3
         ,param4
         ,param5
         ,param6
         ,param7
         ,param8
         ,param9
         ,param10
         ,param11
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      def filelocation(pin,indx_drive,indx_path):
         
         if pin[1:2] == ':' or pin[0:2] == '\\\\':
            return pin;
            
         if pin[0:1] == '\\':
            return indx_drive + pin;
            
         return indx_drive + indx_path + os.sep + pin;
      
      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      else:
      
         if parameters[1].altered and not parameters[1].hasBeenValidated:
            parameters[1].value = arcpy.ValidateTableName(
                name      = parameters[1].valueAsText
               ,workspace = aprx.defaultGeodatabase
            );
         
         if parameters[4].altered and not parameters[4].hasBeenValidated:
         
            if arcpy.Exists(parameters[4].valueAsText):
            
               with open(parameters[4].valueAsText) as json_file:
                  data = json.load(json_file);
               
               indx_drive,indx_path = os.path.splitdrive(parameters[4].valueAsText);
               indx_path,indx_file  = os.path.split(indx_path);
               
               if 'NED' in data:
                  parameters[5].value = filelocation(data['NED'],indx_drive,indx_path);
               if 'SLOPE' in data:
                  parameters[5].value = filelocation(data['SLOPE'],indx_drive,indx_path);
               if 'NLCD' in data:
                  parameters[6].value = filelocation(data['NLCD'],indx_drive,indx_path);
               if 'NHD' in data:
                  parameters[7].value = filelocation(data['NHD'],indx_drive,indx_path);
               if 'TNM' in data:
                  parameters[8].value = filelocation(data['TNM'],indx_drive,indx_path);
               if 'SSURGO' in data:
                  parameters[9].value = filelocation(data['SSURGO'],indx_drive,indx_path);
                  
               parameters[4].value = None;
      
      return;

   #...........................................................................
   def updateMessages(self,parameters):

      return;

   #...........................................................................
   def execute(self,parameters,messages):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      ##---------------------------------------------------------------------##
      aoi_id = arcpy.ValidateTableName(
          name      = parameters[1].valueAsText
         ,workspace = aprx.defaultGeodatabase
      );
      aoi_layer           = parameters[2].value;
      aoi_bypass          = parameters[3].value;
      
      sloperaster         = parameters[5].valueAsText;
      if sloperaster == "" or sloperaster == " ":
         sloperaster = None;
         
      landcoverraster     = parameters[6].valueAsText; 
      if landcoverraster == "" or landcoverraster == " ":
         landcoverraster = None;
         
      nhdfc               = parameters[7].valueAsText;
      if nhdfc == "" or nhdfc == " ":
         nhdfc = None;
         
      roadsfc             = parameters[8].valueAsText;
      if roadsfc == "" or roadsfc == " ":
         roadsfc = None;
         
      ssurgofc            = parameters[9].valueAsText;
      if ssurgofc == "" or ssurgofc == " ":
         ssurgofc = None;
      
      vectorbuffer        = parameters[10].value;
      if vectorbuffer is None:
         vectorbuffer = 0;
         
      notes               = parameters[11].valueAsText;
      if notes == "" or notes == " ":
         notes = None;
 
      if aoi_bypass is not None and aoi_bypass != "":
         aoi_layer = aoi_bypass;
         
      existing_aois = util.fetchAOIIDs();
      if aoi_id in existing_aois:
         raise Exception('AOI ID already exists');
         
      ##---------------------------------------------------------------------##
      # Decide whether to utilize the memory workspace or the scratch workspace
      d = arcpy.GetInstallInfo();
      
      if d['Version'][:3] == '2.3':
         wrkGDB = arcpy.env.scratchGDB;
         
      else:
         wrkGDB = 'memory';
      
      ##---------------------------------------------------------------------##
      arcpy.Dissolve_management(
          in_features       = aoi_layer
         ,out_feature_class = wrkGDB + os.sep + "inMemoryAOI"
      );
      
      try:
         arcpy.AddField_management(
             wrkGDB + os.sep + "inMemoryAOI"
            ,"geodesicArea"
            ,"DOUBLE"
            ,18
         );
      except:
         None;
         
      arcpy.CalculateField_management(
          in_table        = wrkGDB + os.sep + "inMemoryAOI"
         ,field           = "geodesicArea"
         ,expression      = "!shape.geodesicArea@SQUAREKILOMETERS!"
         ,expression_type = "PYTHON_9.3"
      );
      
      num_areasqkm = None;
      with arcpy.da.SearchCursor(
          in_table    = wrkGDB + os.sep + "inMemoryAOI"
         ,field_names = ["geodesicArea"]
      ) as cursor:
         for row in cursor:
            num_areasqkm = row[0];
            
      if num_areasqkm is None \
      or num_areasqkm < 0.05:
         raise Exception("Area of Interest polygons smaller than 0.05 sq km are not valid. (" + str(num_areasqkm) + ")");
      
      else:
         arcpy.AddMessage(".  Area of Interest size: " + str(num_areasqkm) + " sqm.");
         
      ##---------------------------------------------------------------------##
      areaofinterest = AOI(
          aoi_id          = aoi_id
         ,aoi_layer       = wrkGDB + os.sep + "inMemoryAOI"
         ,sloperaster     = sloperaster
         ,landcoverraster = landcoverraster
         ,nhdfc           = nhdfc
         ,roadsfc         = roadsfc
         ,ssurgofc        = ssurgofc
         ,vectorbuffer    = vectorbuffer
         ,notes           = notes
      );

      areaofinterest.loadAOI();
      
      ##---------------------------------------------------------------------##
      util.write_stash({
          "sloperaster"    : sloperaster
         ,"landcoverraster": landcoverraster
         ,"nhdfc"          : nhdfc
         ,"roadsfc"        : roadsfc
         ,"ssurgofc"       : ssurgofc
      });

###############################################################################
class DeleteAOI(object):

   #...........................................................................
   def __init__(self):

      self.label              = "A3 Delete AOI";
      self.name               = "DeleteAOI";
      self.description        = "DeleteAOI";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
         
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
         ary_aois = [];
      else:
         ary_aois = util.fetchAOIIDs(cf=cf);
         if len(ary_aois) == 0:
            err_val   = "No areas of interest found to delete.";
            err_enb  = True;
            parm_enb = False;
      
      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val = "Please save or delete all pending edits before proceeding.";
         err_enb = True;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "AOI ID"
         ,name          = "AOIID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,multiValue    = False
      );
      param1.filter.type = "ValueList";
      param1.filter.list = ary_aois;
      if len(ary_aois) > 0:
         param1.value = ary_aois[0];

      params = [
          param0
         ,param1
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      ##---------------------------------------------------------------------##
      aoi_id = parameters[1].valueAsText;
      cf = util.fetchConfig();

      st = cf['aoistorage'] + os.sep + util.g_aoi_fc;
      if not arcpy.Exists(st):
         msg = "AOI Storage not found [" + st + "]";
         util.dzlog(msg,'error');
         raise arcpy.ExecuteError(msg);

      with arcpy.da.UpdateCursor(st,"aoi_id") as cursor:
         for row in cursor:
            if row[0] == aoi_id:
               cursor.deleteRow();

      util.deleteAOIFiles(aoi_id,cf=cf);

###############################################################################
class RenameAOI(object):

   #...........................................................................
   def __init__(self):

      self.label              = "A4 Rename AOI";
      self.name               = "RenameAOI";
      self.description        = "RenameAOI";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
         
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
         ary_aois = [];
      else:
         ary_aois = util.fetchAOIIDs(cf=cf);
         if len(ary_aois) == 0:
            err_val   = "No areas of interest found to rename.";
            err_enb  = True;
            parm_enb = False;
      
      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val = "Please save or delete all pending edits before proceeding.";
         err_enb = True;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "AOI ID"
         ,name          = "AOIID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,multiValue    = False
      );
      param1.filter.type = "ValueList";
      param1.filter.list = ary_aois;
      if len(ary_aois) > 0:
         param1.value = ary_aois[0];

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "New AOI ID"
         ,name          = "NewAOIID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );

      params = [
          param0
         ,param1
         ,param2
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      if parameters[2].altered and not parameters[2].hasBeenValidated:
         parameters[2].value = arcpy.ValidateTableName(
             name      = parameters[2].valueAsText
            ,workspace = aprx.defaultGeodatabase
         );

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      ##---------------------------------------------------------------------##
      aoi_id     = parameters[1].valueAsText;
      new_aoi_id = arcpy.ValidateTableName(
          name      = parameters[2].valueAsText
         ,workspace = aprx.defaultGeodatabase
      );
      cf = util.fetchConfig();

      st = cf['aoistorage'] + os.sep + util.g_aoi_fc;
      if not arcpy.Exists(st):
         msg = "AOI Storage not found [" + st + "]";
         util.dzlog(msg,'error');
         raise arcpy.ExecuteError(msg);

      with arcpy.da.UpdateCursor(st,"aoi_id") as cursor:
         for row in cursor:
            if row[0] == new_aoi_id:
               cursor.deleteRow();

      with arcpy.da.UpdateCursor(
          st
         ,[
             'aoi_id'
            ,'sloperaster'          
            ,'landcoverraster'      
            ,'nhdfc'                
            ,'roadsfc'              
            ,'ssurgofc'
          ]
      ) as cursor:
         for row in cursor:
            if row[0] == aoi_id:
               row[0] = new_aoi_id;
               row[1] = new_aoi_id + "_SLOPE"
               row[2] = new_aoi_id + "_LANDCOVER"
               row[3] = new_aoi_id + "_NHD"
               row[4] = new_aoi_id + "_ROADS"
               row[5] = new_aoi_id + "_SSURGO"
               cursor.updateRow(row);

      if arcpy.Exists(cf['aoistorage'] + os.sep + new_aoi_id + "_SLOPE"):
         arcpy.Delete_management(cf['aoistorage'] + os.sep + new_aoi_id + "_SLOPE");
      if arcpy.Exists(cf['aoistorage'] + os.sep + new_aoi_id + "_LANDCOVER"):
         arcpy.Delete_management(cf['aoistorage'] + os.sep + new_aoi_id + "_LANDCOVER");
      if arcpy.Exists(cf['aoistorage'] + os.sep + new_aoi_id + "_NHD"):
         arcpy.Delete_management(cf['aoistorage'] + os.sep + new_aoi_id + "_NHD");
      if arcpy.Exists(cf['aoistorage'] + os.sep + new_aoi_id + "_ROADS"):
         arcpy.Delete_management(cf['aoistorage'] + os.sep + new_aoi_id + "_ROADS");
      if arcpy.Exists(cf['aoistorage'] + os.sep + new_aoi_id + "_SSURGO"):
         arcpy.Delete_management(cf['aoistorage'] + os.sep + new_aoi_id + "_SSURGO");

      if arcpy.Exists(cf['aoistorage'] + os.sep + aoi_id + "_SLOPE"):
         arcpy.Rename_management(
             cf['aoistorage'] + os.sep + aoi_id + "_SLOPE"
            ,cf['aoistorage'] + os.sep + new_aoi_id + "_SLOPE"
         );

      if arcpy.Exists(cf['aoistorage'] + os.sep + aoi_id + "_LANDCOVER"):
         arcpy.Rename_management(
             cf['aoistorage'] + os.sep + aoi_id + "_LANDCOVER"
            ,cf['aoistorage'] + os.sep + new_aoi_id + "_LANDCOVER"
         );

      if arcpy.Exists(cf['aoistorage'] + os.sep + aoi_id + "_NHD"):
         arcpy.Rename_management(
             cf['aoistorage'] + os.sep + aoi_id + "_NHD"
            ,cf['aoistorage'] + os.sep + new_aoi_id + "_NHD"
         );

      if arcpy.Exists(cf['aoistorage'] + os.sep + aoi_id + "_ROADS"):
         arcpy.Rename_management(
             cf['aoistorage'] + os.sep + aoi_id + "_ROADS"
            ,cf['aoistorage'] + os.sep + new_aoi_id + "_ROADS"
         );

      if arcpy.Exists(cf['aoistorage'] + os.sep + aoi_id + "_SSURGO"):
         arcpy.Rename_management(
             cf['aoistorage'] + os.sep + aoi_id + "_SSURGO"
            ,cf['aoistorage'] + os.sep + new_aoi_id + "_SSURGO"
         );

###############################################################################
class ScenarioSetup(object):

   #...........................................................................
   def __init__(self):

      self.label              = "B1 Scenario Setup";
      self.name               = "ScenarioSetup";
      self.description        = "ScenarioSetup";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
      
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
      
      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val = "Please save or delete all pending edits before proceeding.";
         err_enb = True;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "Purge Existing Scenarios"
         ,name          = "PurgeExistingScenarios"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param1.value = False;

      params = [
          param0
         ,param1
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);

      ##---------------------------------------------------------------------##
      if parameters[1].valueAsText == "true":
         boo_purge = True;
      else:
         boo_purge = False;

      ##---------------------------------------------------------------------##
      if not arcpy.Exists(aprx.defaultGeodatabase):
         pf = os.path.split(aprx.defaultGeodatabase);
         arcpy.CreateFileGDB_management(
             out_folder_path = pf[0]
            ,out_name        = pf[1]
         );

      ##---------------------------------------------------------------------##
      fc = aprx.defaultGeodatabase + os.sep + util.g_scenario_fc;
      if not arcpy.Exists(fc):

         util.dzlog("Creating Scenarios feature class at " + str(fc) + ".");

         arcpy.env.workspace = aprx.defaultGeodatabase;
         arcpy.CreateFeatureclass_management(
             out_path          = aprx.defaultGeodatabase
            ,out_name          = util.g_scenario_fc
            ,geometry_type     = "POLYGON"
            ,has_m             = "DISABLED"
            ,has_z             = "DISABLED"
            ,spatial_reference = arcpy.SpatialReference(util.g_srid)
            ,config_keyword    = None
         );
         
         arcpy.management.AddFields(
             util.g_scenario_fc
            ,[
                ['scenario_id'                      ,'TEXT'  ,'Scenario ID'                        ,255, None,'']
               ,['analysis_complete'                ,'TEXT'  ,'Analysis Complete Flag'             ,1,   None,'']
               ,['aoi_id'                           ,'TEXT'  ,'Area of Interest ID'                ,255, None,'']
               ,['load_slope'                       ,'TEXT'  ,'Load Slope Flag'                    ,1,   None,'']
               ,['load_landcover'                   ,'TEXT'  ,'Load Land Cover Flag'               ,1,   None,'']
               ,['load_nhd'                         ,'TEXT'  ,'Load NHD Flag'                      ,1,   None,'']
               ,['load_roads'                       ,'TEXT'  ,'Load Roads Flag'                    ,1,   None,'']
               ,['load_ssurgo'                      ,'TEXT'  ,'Load SSURGO Flag'                   ,1,   None,'']
               ,['slopegridsize'                    ,'DOUBLE','Slope Grid Size (m2)'               ,None,None,'']
               ,['landcovergridsize'                ,'DOUBLE','Land Cover Grid Size (m2)'          ,None,None,'']
               ,['nhdgridsize'                      ,'DOUBLE','NHD Grid Size (m2)'                 ,None,None,'']
               ,['roadsgridsize'                    ,'DOUBLE','Roads Grid Size (m2)'               ,None,None,'']
               ,['ssurgogridsize'                   ,'DOUBLE','SSURGO Grid Size (m2)'              ,None,None,'']
               ,['slopereclassification'            ,'TEXT'  ,'Slope Reclassification'             ,2000,None,'']
               ,['landcoverreclassification'        ,'TEXT'  ,'Land Cover Reclassification'        ,2000,None,'']
               ,['nhdreclassification'              ,'TEXT'  ,'NHD Reclassification'               ,2000,None,'']
               ,['roadsreclassification'            ,'TEXT'  ,'Roads Reclassification'             ,2000,None,'']
               ,['ssurgoreclassification'           ,'TEXT'  ,'SSURGO Reclassification'            ,2000,None,'']
               ,['slopeweight'                      ,'TEXT'  ,'Slope Weight'                       ,2000,None,'']
               ,['landcoverweight'                  ,'TEXT'  ,'Land Cover Weight'                  ,2000,None,'']
               ,['nhdweight'                        ,'TEXT'  ,'NHD Weight'                         ,2000,None,'']
               ,['roadsweight'                      ,'TEXT'  ,'Roads Weight'                       ,2000,None,'']
               ,['ssurgoweight'                     ,'TEXT'  ,'SSURGO Weight'                      ,2000,None,'']
               ,['selected_featurecount'            ,'LONG'  ,'Selected Feature Count'             ,None,None,'']
               ,['selected_areasqkm'                ,'DOUBLE','Selected Area (sqkm)'               ,None,None,'']
               ,['mean_suitability_score'           ,'DOUBLE','Mean Suitability Score'             ,None,None,'']
               ,['available_solid_waste_capacity_m3','DOUBLE','Available Solid Waste Capacity (m3)',None,None,'']
               ,['available_liquid_waste_capacity_L','DOUBLE','Available Liquid Waste Capacity (L)',None,None,'']
               ,['username'                         ,'TEXT'  ,'User Name'                          ,255, None,'']
               ,['datecreated'                      ,'DATE'  ,'Date Created'                       ,None,None,'']
               ,['lastupdate'                       ,'DATE'  ,'Date Last Updated'                  ,None,None,'']
               ,['notes'                            ,'TEXT'  ,'Notes'                              ,255, None,'']
             ]
         );

      ##---------------------------------------------------------------------##
      if boo_purge:
         with arcpy.da.UpdateCursor(fc,"scenario_id") as cursor:
            for row in cursor:
               util.deleteScenarioFiles(row[0],aprx=None);
               cursor.deleteRow();

###############################################################################
class LoadNewScenario(object):

   #...........................................................................
   def __init__(self):

      self.label              = "B2 Load New Scenario";
      self.name               = "LoadNewScenario";
      self.description        = "LoadNewScenario";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
      
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
         scenarios = [];
         ary_aois  = [];
         
      else:
         if not util.checkScenarioSystem(aprx=aprx):
            err_val   = "Scenario Storage has not been initialized.";
            err_enb  = True;
            parm_enb = False;
            scenarios = [];
            ary_aois  = [];
            
         else:
            ary_aois = util.fetchAOIIDs();
            if len(ary_aois) == 0:
               err_val  = "No areas of interest loaded from which to create scenarios.";
               err_enb  = True;
               parm_enb = False;
      
      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val = "Please save or delete all pending edits before proceeding.";
         err_enb = True;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "Scenario ID"
         ,name          = "ScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "AOI ID"
         ,name          = "AOIID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,multiValue    = False
      );
      param2.filter.type = "ValueList";
      param2.filter.list = ary_aois;
      if len(ary_aois) > 0:
         param2.value = ary_aois[0];

      ##---------------------------------------------------------------------##
      param3 = arcpy.Parameter(
          displayName   = "Load NED Slope"
         ,name          = "LoadNEDSlope"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param3.value = True;

      ##---------------------------------------------------------------------##
      param4 = arcpy.Parameter(
          displayName   = "Load Land Cover"
         ,name          = "LoadLandCover"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param4.value = True;

      ##---------------------------------------------------------------------##
      param5 = arcpy.Parameter(
          displayName   = "Load NHD"
         ,name          = "LoadNHD"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param5.value = True;

      ##---------------------------------------------------------------------##
      param6 = arcpy.Parameter(
          displayName   = "NHD Grid Size (m2)"
         ,name          = "NHDGridSize"
         ,datatype      = "GPDouble"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param6.value = util.g_default_nhdgridsize;

      ##---------------------------------------------------------------------##
      param7 = arcpy.Parameter(
          displayName   = "Load TNM Roads"
         ,name          = "LoadTNMRoads"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param7.value = True;

      ##---------------------------------------------------------------------##
      param8 = arcpy.Parameter(
          displayName   = "TNM Roads Grid Size (m2)"
         ,name          = "TNMRoadsGridSize"
         ,datatype      = "GPDouble"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param8.value = util.g_default_tnmroadsgridsize;

      ##---------------------------------------------------------------------##
      param9 = arcpy.Parameter(
          displayName   = "Load SSURGO"
         ,name          = "LoadSSURGO"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param9.value = True;

      ##---------------------------------------------------------------------##
      param10 = arcpy.Parameter(
          displayName   = "SSURGO Grid Size (m2)"
         ,name          = "EsriSSURGOGridSize"
         ,datatype      = "GPDouble"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param10.value = util.g_default_ssurgogridsize;

      ##---------------------------------------------------------------------##
      param11 = arcpy.Parameter(
          displayName   = "Optional Notes"
         ,name          = "OptionalNotes"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );

      params = [
          param0
         ,param1
         ,param2
         ,param3
         ,param4
         ,param5
         ,param6
         ,param7
         ,param8
         ,param9
         ,param10
         ,param11
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      if parameters[1].altered and not parameters[1].hasBeenValidated:
         parameters[1].value = arcpy.ValidateTableName(
             name      = parameters[1].valueAsText
            ,workspace = aprx.defaultGeodatabase
         );

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      ##---------------------------------------------------------------------##
      scenario_id = arcpy.ValidateTableName(
          name      = parameters[1].valueAsText
         ,workspace = aprx.defaultGeodatabase
      );
      if scenario_id == "" or scenario_id == " ":
         scenario_id = None;
      
      aoi_id = parameters[2].valueAsText;
      if aoi_id == "" or aoi_id == " ":
         aoi_id = None;

      if parameters[3].valueAsText == "true":
         boo_load_slope = True;
      else:
         boo_load_slope = False;

      if parameters[4].valueAsText == "true":
         boo_load_landcover = True;
      else:
         boo_load_landcover = False;

      if parameters[5].valueAsText == "true":
         boo_load_nhd = True;
      else:
         boo_load_nhd = False;

      num_nhdgridsize = parameters[6].value;

      if parameters[7].valueAsText == "true":
         boo_load_roads = True;
      else:
         boo_load_roads = False;

      num_roadsgridsize = parameters[8].value;

      if parameters[9].valueAsText == "true":
         boo_load_ssurgo = True;
      else:
         boo_load_ssurgo = False;

      num_ssurgogridsize = parameters[10].value;
      
      str_notes = parameters[11].valueAsText;

      ##---------------------------------------------------------------------##
      cf = util.fetchConfig();

      scenario = Scenario(
         scenario_id = scenario_id
      );
      scenario.load(
          aoi_id         = aoi_id
         ,load_slope     = boo_load_slope
         ,load_landcover = boo_load_landcover
         ,load_nhd       = boo_load_nhd
         ,nhdgridsize    = num_nhdgridsize
         ,load_roads     = boo_load_roads
         ,roadsgridsize  = num_roadsgridsize
         ,load_ssurgo    = boo_load_ssurgo
         ,ssurgogridsize = num_ssurgogridsize
         ,notes          = str_notes
         ,cf             = cf
         ,aprx           = aprx
      );

###############################################################################
class DeleteScenario(object):

   #...........................................................................
   def __init__(self):

      self.label              = "B3 Delete Scenario";
      self.name               = "DeleteScenario";
      self.description        = "DeleteScenario";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
      
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
         scenarios = [];
         def_scenario = None;
         
      else:
         if not util.checkScenarioSystem(aprx=aprx):
            err_val   = "Scenario Storage has not been initialized.";
            err_enb  = True;
            parm_enb = False;
            scenarios = [];
            def_scenario = None;
            
         else:
            scenarios,def_scenario = util.fetchScenarioIDs(aprx=aprx);
            if len(scenarios) == 0:
               err_val   = "No scenarios found to delete.";
               err_enb  = True;
               parm_enb = False;
      
      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val = "Please save or delete all pending edits before proceeding.";
         err_enb = True;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "Scenario ID"
         ,name          = "ScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,multiValue    = False
      );
      param1.filter.type = "ValueList";
      param1.filter.list = scenarios;
      param1.value       = def_scenario;

      params = [
          param0
         ,param1
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      ##---------------------------------------------------------------------##
      scenario_id = parameters[1].valueAsText;
      util.deleteScenarioID(scenario_id);

###############################################################################
class RenameScenario(object):

   #...........................................................................
   def __init__(self):

      self.label              = "B4 Rename Scenario";
      self.name               = "RenameScenario";
      self.description        = "RenameScenario";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
      
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
         scenarios = [];
         def_scenario = None;
         
      else:
         if not util.checkScenarioSystem(aprx=aprx):
            err_val   = "Scenario Storage has not been initialized.";
            err_enb  = True;
            parm_enb = False;
            scenarios = [];
            def_scenario = None;
            
         else:
            scenarios,def_scenario = util.fetchScenarioIDs(aprx=aprx);
            if len(scenarios) == 0:
               err_val   = "No scenarios found to rename.";
               err_enb  = True;
               parm_enb = False;
      
      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val = "Please save or delete all pending edits before proceeding.";
         err_enb = True;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "Scenario ID"
         ,name          = "ScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,multiValue    = False
      );
      param1.filter.type = "ValueList";
      param1.filter.list = scenarios;
      param1.value       = def_scenario;

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "New Scenario ID"
         ,name          = "NewScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,multiValue    = False
      );

      params = [
          param0
         ,param1
         ,param2
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      if parameters[2].altered and not parameters[2].hasBeenValidated:
         parameters[2].value = arcpy.ValidateTableName(
             name      = parameters[2].valueAsText
            ,workspace = aprx.defaultGeodatabase
         );

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);

      ##---------------------------------------------------------------------##
      scenario_id     = parameters[1].valueAsText;
      new_scenario_id = arcpy.ValidateTableName(
          name      = parameters[2].valueAsText
         ,workspace = aprx.defaultGeodatabase
      );

      util.deleteScenarioID(new_scenario_id,aprx=aprx);
      util.deleteScenarioFiles(new_scenario_id,aprx=aprx);
      
      with arcpy.da.UpdateCursor(
          aprx.defaultGeodatabase + os.sep + util.g_scenario_fc
         ,[
             'scenario_id'
            ,'lastupdate'
          ]
      ) as cursor:
         for row in cursor:
            if row[0] == scenario_id:
               row[0] = new_scenario_id;
               row[1] = datetime.datetime.now();
               cursor.updateRow(row);

      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_SLOPE"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_SLOPE"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_EXTRACT_SLOPE"
         );
      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_LANDCOVER"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_LANDCOVER"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_EXTRACT_LANDCOVER"
         );
      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_NHD"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_NHD"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_EXTRACT_NHD"
         );
      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_ROADS"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_ROADS"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_EXTRACT_ROADS"
         );
      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_SSURGO"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_SSURGO"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_EXTRACT_SSURGO"
         );

      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_SLOPE"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_SLOPE"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_RECLASS_SLOPE"
         );
      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_LANDCOVER"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_LANDCOVER"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_RECLASS_LANDCOVER"
         );
      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_NHD"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_NHD"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_RECLASS_NHD"
         );
      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_ROADS"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_ROADS"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_RECLASS_ROADS"
         );
      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_SSURGO"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_SSURGO"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_RECLASS_SSURGO"
         );

      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_WEIGHTEDSUM"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_WEIGHTEDSUM"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_WEIGHTEDSUM"
         );
      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_STAGINGSITESELECTION"):
         arcpy.Rename_management(
             aprx.defaultGeodatabase + os.sep + scenario_id + "_STAGINGSITESELECTION"
            ,aprx.defaultGeodatabase + os.sep + new_scenario_id + "_STAGINGSITESELECTION"
         );
         
###############################################################################
class DuplicateScenario(object):

   #...........................................................................
   def __init__(self):

      self.label              = "B5 Duplicate Scenario";
      self.name               = "DuplicateScenario";
      self.description        = "DuplicateScenario";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
      
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
         scenarios = [];
         def_scenario = None;
         
      else:
         if not util.checkScenarioSystem(aprx=aprx):
            err_val   = "Scenario Storage has not been initialized.";
            err_enb  = True;
            parm_enb = False;
            scenarios = [];
            def_scenario = None;
            
         else:
            scenarios,def_scenario = util.fetchScenarioIDs(aprx=aprx);
            if len(scenarios) == 0:
               err_val   = "No scenarios found to duplicate.";
               err_enb  = True;
               parm_enb = False;

      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val = "Please save or delete all pending edits before proceeding.";
         err_enb = True;
         
      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "Scenario ID"
         ,name          = "ScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,multiValue    = False
      );
      param1.filter.type = "ValueList";
      param1.filter.list = scenarios;
      param1.value       = def_scenario;

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "New Scenario ID"
         ,name          = "NewScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,multiValue    = False
      );

      params = [
          param0
         ,param1
         ,param2
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);

      ##---------------------------------------------------------------------##
      scenario_id     = parameters[1].valueAsText;
      new_scenario_id = parameters[2].valueAsText;

      util.deleteScenarioID(new_scenario_id,aprx=aprx);
      util.deleteScenarioFiles(new_scenario_id,aprx=aprx);
      
      flds = [
          'scenario_id'
         ,'analysis_complete'
         ,'aoi_id'
         ,'slopegridsize'
         ,'landcovergridsize'
         ,'nhdgridsize'
         ,'roadsgridsize'
         ,'ssurgogridsize'
         ,'slopereclassification'
         ,'landcoverreclassification'
         ,'nhdreclassification'
         ,'roadsreclassification'
         ,'ssurgoreclassification'
         ,'slopeweight'
         ,'landcoverweight'
         ,'nhdweight'
         ,'roadsweight'
         ,'ssurgoweight'
         ,'selected_featurecount'
         ,'selected_areasqkm'
         ,'mean_suitability_score'
         ,'available_solid_waste_capacity_m3'
         ,'available_liquid_waste_capacity_L'
         ,'username'
         ,'datecreated'
         ,'lastupdate'
         ,'notes'
         ,'SHAPE@'
      ];
      
      drow = None;
      with arcpy.da.SearchCursor(
          aprx.defaultGeodatabase + os.sep + util.g_scenario_fc
         ,flds
      ) as cursor:
         for row in cursor:
            if row[0] is not None and row[0] == scenario_id:
               drow = row;
               
      if drow is not None:
         with arcpy.da.InsertCursor(
             aprx.defaultGeodatabase + os.sep + util.g_scenario_fc
            ,flds
         ) as cursor:         
            cursor.insertRow((
                new_scenario_id
               ,drow[1]
               ,drow[2]
               ,drow[3]
               ,drow[4]
               ,drow[5]
               ,drow[6]
               ,drow[7]
               ,drow[8]
               ,drow[9]
               ,drow[10]
               ,drow[11]
               ,drow[12]
               ,drow[13]
               ,drow[14]
               ,drow[15]
               ,drow[16]
               ,drow[17]
               ,drow[18]
               ,drow[19]
               ,drow[20]
               ,drow[21]
               ,drow[22]
               ,drow[23]
               ,drow[24]
               ,drow[25]
               ,drow[26]
               ,drow[27]
            ));
      
         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_SLOPE"):
            arcpy.CopyRaster_management(
                in_raster         = aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_SLOPE"
               ,out_rasterdataset = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_EXTRACT_SLOPE"
            );
            
         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_LANDCOVER"):
            arcpy.CopyRaster_management(
                in_raster         = aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_LANDCOVER"
               ,out_rasterdataset = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_EXTRACT_LANDCOVER"
            );
            
         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_NHD"):
            arcpy.CopyRaster_management(
                in_raster         = aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_NHD"
               ,out_rasterdataset = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_EXTRACT_NHD"
            );
            
         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_ROADS"):
            arcpy.CopyRaster_management(
                in_raster         = aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_ROADS"
               ,out_rasterdataset = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_EXTRACT_ROADS"
            );
            
         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_SSURGO"):
            arcpy.CopyRaster_management(
                in_raster         = aprx.defaultGeodatabase + os.sep + scenario_id + "_EXTRACT_SSURGO"
               ,out_rasterdataset = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_EXTRACT_SSURGO"
            );

         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_SLOPE"):
            arcpy.CopyRaster_management(
                in_raster         = aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_SLOPE"
               ,out_rasterdataset = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_RECLASS_SLOPE"
            );
            
         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_LANDCOVER"):
            arcpy.CopyRaster_management(
                in_raster         = aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_LANDCOVER"
               ,out_rasterdataset = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_RECLASS_LANDCOVER"
            );
            
         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_NHD"):
            arcpy.CopyRaster_management(
                in_raster         = aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_NHD"
               ,out_rasterdataset = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_RECLASS_NHD"
            );
            
         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_ROADS"):
            arcpy.CopyRaster_management(
                in_raster         = aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_ROADS"
               ,out_rasterdataset = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_RECLASS_ROADS"
            );
            
         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_SSURGO"):
            arcpy.CopyRaster_management(
                in_raster         = aprx.defaultGeodatabase + os.sep + scenario_id + "_RECLASS_SSURGO"
               ,out_rasterdataset = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_RECLASS_SSURGO"
            );

         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_WEIGHTEDSUM"):
            arcpy.CopyFeatures_management(
                in_features       = aprx.defaultGeodatabase + os.sep + scenario_id + "_WEIGHTEDSUM"
               ,out_feature_class = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_WEIGHTEDSUM"
            );
            
         if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + "_STAGINGSITESELECTION"):
            arcpy.CopyFeatures_management(
                in_features       = aprx.defaultGeodatabase + os.sep + scenario_id + "_STAGINGSITESELECTION"
               ,out_feature_class = aprx.defaultGeodatabase + os.sep + new_scenario_id + "_STAGINGSITESELECTION"
            );

###############################################################################
class AddScenarioToMap(object):

   #...........................................................................
   def __init__(self):

      self.label              = "C1 Add Scenario To Map";
      self.name               = "AddScenarioToMap";
      self.description        = "AddScenarioToMap";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
      
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
         scenarios = [];
         def_scenario = None;
         
      else:
         if not util.checkScenarioSystem(aprx=aprx):
            err_val   = "Scenario Storage has not been initialized.";
            err_enb  = True;
            parm_enb = False;
            scenarios = [];
            def_scenario = None;
            
         else:
            scenarios,def_scenario = util.fetchScenarioIDs(aprx=aprx);
            if len(scenarios) == 0:
               err_val   = "No scenarios found to add to map.";
               err_enb  = True;
               parm_enb = False;

      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val   = "Please save or delete all pending edits before proceeding.";
         err_enb   = True;
         parm_enb  = False;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "Scenario ID"
         ,name          = "ScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,multiValue    = False
      );
      param1.filter.type = "ValueList";
      param1.filter.list = scenarios;
      param1.value       = def_scenario;

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "Map Name"
         ,name          = "MapName"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      map_objs = aprx.listMaps('*');
      maps = [];
      for item in map_objs:
         maps.append(item.name);
      param2.filter.type = "ValueList";
      param2.filter.list = maps;
      if len(maps) > 0:
         param2.value = aprx.activeMap.name;
 
      params = [
          param0
         ,param1
         ,param2
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);

      ##---------------------------------------------------------------------##
      scenario_id = parameters[1].valueAsText;
      map_name    = parameters[2].valueAsText;

      map = aprx.listMaps(map_name)[0];
      if map is None:
         raise Exception("map not found");

      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + '_WEIGHTEDSUM'):
         lyrx = util.tempLyrx(
             in_layerfile = os.path.join(aprx.homeFolder,"WeightedSum.lyrx")
            ,dataset      = scenario_id + "_WEIGHTEDSUM"
            ,name         = scenario_id + "_WeightedSum"
            ,aprx         = aprx
         );
         lyr = arcpy.mp.LayerFile(lyrx);
         map.addLayer(lyr);
      
      else:
         arcpy.AddMessage("No weighted analysis layer found for scenario " + str(scenario_id));

      if arcpy.Exists(aprx.defaultGeodatabase + os.sep + scenario_id + '_STAGINGSITESELECTION'):
         lyrx = util.tempLyrx(
             in_layerfile = os.path.join(aprx.homeFolder,"StagingSiteSelection.lyrx")
            ,dataset      = scenario_id + "_STAGINGSITESELECTION"
            ,name         = scenario_id + "_StagingSiteSelection"
            ,aprx         = aprx
         );
         lyr = arcpy.mp.LayerFile(lyrx);
         map.addLayer(lyr);
         
      else:
         arcpy.AddMessage("No staging site selection layer found for scenario " + str(scenario_id));

###############################################################################
class RasterToResults(object):

   #...........................................................................
   def __init__(self):

      self.label              = "C2 Raster To Results";
      self.name               = "RasterToResults";
      self.description        = "RasterToResults";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
      
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
         scenarios = [];
         def_scenario = None;
         
      else:
         if not util.checkScenarioSystem(aprx=aprx):
            err_val   = "Scenario Storage has not been initialized.";
            err_enb  = True;
            parm_enb = False;
            scenarios = [];
            def_scenario = None;
            
         else:
            scenarios,def_scenario = util.fetchScenarioIDs(aprx=aprx);
            if len(scenarios) == 0:
               err_val   = "No scenarios found to add to map.";
               err_enb  = True;
               parm_enb = False;

      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val   = "Please save or delete all pending edits before proceeding.";
         err_enb   = True;
         parm_enb  = False;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "Input Raster"
         ,name          = "InputRaster"
         ,datatype      = "DERasterDataset"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,multiValue    = False
      );
      
      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "Simplify Polygons"
         ,name          = "Simplify Polygons"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param2.value = True;

      ##---------------------------------------------------------------------##
      param3 = arcpy.Parameter(
          displayName   = "Output Feature Class"
         ,name          = "OutputFeatureClass"
         ,datatype      = "DEFeatureClass"
         ,parameterType = "Required"
         ,direction     = "Output"
         ,enabled       = parm_enb
      );
 
      params = [
          param0
         ,param1
         ,param2
         ,param3
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      return;

   #...........................................................................
   def execute(self,parameters,messages):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);

      ##---------------------------------------------------------------------##
      input_raster = parameters[1].valueAsText;
      
      str_simplify = parameters[2].valueAsText;
      if str_simplify in ['true','TRUE','1','Yes','Y']:
         str_simplify = 'SIMPLIFY';
      else:
         str_simplify = 'NO_SIMPLIFY'; 
         
      output_fc = parameters[3].valueAsText;
      
      ##---------------------------------------------------------------------##
      rez = arcpy.RasterToPolygon_conversion(
          in_raster            = input_raster
         ,out_polygon_features = output_fc
         ,simplify             = str_simplify
         ,field                = "suitability_score"
         ,raster_field         = "VALUE"
      );
      
      if rez.status == 4:
         arcpy.AddMessage(".  Polygon conversion completed successfully.");
      else:
         raise Error("raster to polygon process failed with status " + str(rez.status));
         
      util.addField(
          in_table          = output_fc
         ,field_name        = "name"
         ,field_type        = "TEXT"
         ,field_alias       = "Name"
         ,field_is_nullable = True
      );

      util.addField(
          in_table          = output_fc
         ,field_name        = "contamination_type"
         ,field_type        = "TEXT"
         ,field_alias       = "Contamination Type"
         ,field_is_nullable = True
      );

      arcpy.AlterField_management(
          in_table          = output_fc
         ,field             = 'suitability_score'
         ,new_field_alias   = 'Suitability Score'
      );

      util.addFieldCalc(
          in_table          = output_fc
         ,field_name        = "areasqkm"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Geodetic Area (SqKm)"
         ,field_is_nullable = True
         ,calc_value        = "!Shape.geodesicArea@SQUAREKILOMETERS!"
      );

      util.addFieldCalc(
          in_table          = output_fc
         ,field_name        = "available_solid_waste_capacity_m3"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Available Solid Waste Capacity (m3)"
         ,field_is_nullable = True
         ,calc_value        = "!areasqkm! * 1000000 * 0.4 / 0.3284"
      );

      util.addFieldCalc(
          in_table          = output_fc
         ,field_name        = "available_liquid_waste_capacity_L"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Available Liquid Waste Capacity (L)"
         ,field_is_nullable = True
         ,calc_value        = "!areasqkm! * 1000000 * 0.4 / 0.0020975"
      );
      
      util.addFieldCalc(
          in_table          = output_fc
         ,field_name        = "available_liquid_waste_capacity_m3"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Available Liquid Waste Capacity (m3)"
         ,field_is_nullable = True
         ,calc_value        = "(!areasqkm! * 1000000 * 0.4 / 0.0020975) * 0.001"
      );
      
      util.addField(
          in_table          = output_fc
         ,field_name        = "notes"
         ,field_type        = "TEXT"
         ,field_alias       = "Notes"
         ,field_is_nullable = True
      );
      
###############################################################################
class PolygonToResults(object):

   #...........................................................................
   def __init__(self):

      self.label              = "C3 Polygon To Results";
      self.name               = "PolygonToResults";
      self.description        = "PolygonToResults";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      err_val  = None;
      err_enb  = False;
      parm_enb = True;
      
      cf = util.fetchConfig();
      
      if not util.checkAOISystem(cf=cf):
         err_val  = "Areas of interest system has not been setup";
         err_enb  = True;
         parm_enb = False;
         scenarios = [];
         def_scenario = None;
         
      else:
         if not util.checkScenarioSystem(aprx=aprx):
            err_val   = "Scenario Storage has not been initialized.";
            err_enb  = True;
            parm_enb = False;
            scenarios = [];
            def_scenario = None;
            
         else:
            scenarios,def_scenario = util.fetchScenarioIDs(aprx=aprx);
            if len(scenarios) == 0:
               err_val   = "No scenarios found to add to map.";
               err_enb  = True;
               parm_enb = False;

      #########################################################################
      if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
         err_val   = "Please save or delete all pending edits before proceeding.";
         err_enb   = True;
         parm_enb  = False;

      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      ##---------------------------------------------------------------------##
      param1 = arcpy.Parameter(
          displayName   = "Output Feature Class"
         ,name          = "OutputFeatureClass"
         ,datatype      = "DEFeatureClass"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
 
      params = [
          param0
         ,param1
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      return;

   #...........................................................................
   def updateMessages(self,parameters):

      return;

   #...........................................................................
   def execute(self,parameters,messages):

      aprx = arcpy.mp.ArcGISProject(util.g_prj);

      ##---------------------------------------------------------------------##
      input_raster = parameters[1].valueAsText;
      
      str_simplify = parameters[2].valueAsText;
      if str_simplify in ['true','TRUE','1','Yes','Y']:
         str_simplify = 'SIMPLIFY';
      else:
         str_simplify = 'NO_SIMPLIFY'; 
         
      output_fc = parameters[3].valueAsText;
      
      ##---------------------------------------------------------------------##
      rez = arcpy.RasterToPolygon_conversion(
          in_raster            = input_raster
         ,out_polygon_features = output_fc
         ,simplify             = str_simplify
         ,field                = "suitability_score"
         ,raster_field         = "VALUE"
      );
      
      if rez.status == 4:
         arcpy.AddMessage(".  Polygon conversion completed successfully.");
      else:
         raise Error("raster to polygon process failed with status " + str(rez.status));
         
      util.addField(
          in_table          = output_fc
         ,field_name        = "name"
         ,field_type        = "TEXT"
         ,field_alias       = "Name"
         ,field_is_nullable = True
      );

      util.addField(
          in_table          = output_fc
         ,field_name        = "contamination_type"
         ,field_type        = "TEXT"
         ,field_alias       = "Contamination Type"
         ,field_is_nullable = True
      );

      arcpy.AlterField_management(
          in_table          = output_fc
         ,field             = 'suitability_score'
         ,new_field_alias   = 'Suitability Score'
      );

      util.addFieldCalc(
          in_table          = output_fc
         ,field_name        = "areasqkm"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Geodetic Area (SqKm)"
         ,field_is_nullable = True
         ,calc_value        = "!Shape.geodesicArea@SQUAREKILOMETERS!"
      );

      util.addFieldCalc(
          in_table          = output_fc
         ,field_name        = "available_solid_waste_capacity_m3"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Available Solid Waste Capacity (m3)"
         ,field_is_nullable = True
         ,calc_value        = "!areasqkm! * 1000000 * 0.4 / 0.3284"
      );

      util.addFieldCalc(
          in_table          = output_fc
         ,field_name        = "available_liquid_waste_capacity_L"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Available Liquid Waste Capacity (L)"
         ,field_is_nullable = True
         ,calc_value        = "!areasqkm! * 1000000 * 0.4 / 0.0020975"
      );
      
      util.addFieldCalc(
          in_table          = output_fc
         ,field_name        = "available_liquid_waste_capacity_m3"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Available Liquid Waste Capacity (m3)"
         ,field_is_nullable = True
         ,calc_value        = "(!areasqkm! * 1000000 * 0.4 / 0.0020975) * 0.001"
      );
      
      util.addField(
          in_table          = output_fc
         ,field_name        = "notes"
         ,field_type        = "TEXT"
         ,field_alias       = "Notes"
         ,field_is_nullable = True
      );

###############################################################################
class AOI(object):

   #...........................................................................
   def __init__(self
       ,sample_input=None
       ,aoi_id=None
       ,aoi_layer=None
       ,sloperaster=None
       ,landcoverraster=None
       ,nhdfc=None
       ,roadsfc=None
       ,ssurgofc=None
       ,notes=None
       ,vectorbuffer=None
       ,cf=None
   ):
      if sample_input is not None:
         self.aoi_id          = sample_input['aoi_id'];
         self.zipfile         = sample_input['zipfile'];
         self.filegdb         = sample_input['filegdb'];
         self.aoifc           = sample_input['aoifc'];
         self.loadslope       = sample_input['loadslope'];
         self.sloperaster     = sample_input['sloperaster'];
         self.loadlandcover   = sample_input['loadlandcover'];
         self.landcoverraster = sample_input['landcoverraster'];
         self.loadnhd         = sample_input['loadnhd'];
         self.nhdfc           = sample_input['nhdfc'];
         self.loadroads       = sample_input['loadroads'];
         self.roadsfc         = sample_input['roadsfc'];
         self.loadssurgo      = sample_input['loadssurgo'];
         self.ssurgofc        = sample_input['ssurgofc'];
         self.username        = sample_input['username'];
         self.datecreated     = sample_input['datecreated'];
         self.vectorbuffer    = sample_input['vectorbuffer'];
         self.notes           = sample_input['notes'];
         self.zipfile         = util.g_pn + os.sep + 'SampleData' + os.sep + sample_input['zipfile'];
         self.fgdb            = util.g_temp + os.sep + sample_input['filegdb'];

      else:

         self.aoi_id          = aoi_id;
         self.aoifc           = aoi_layer;
         self.sloperaster     = sloperaster;
         if sloperaster:
            self.loadslope = True;
         else:
            self.loadslope = False;
            
         self.landcoverraster = landcoverraster;
         if landcoverraster:
            self.loadlandcover = True;
         else:
            self.loadlandcover = False;
            
         self.nhdfc           = nhdfc;
         if nhdfc:
            self.loadnhd = True;
         else:
            self.loadnhd = False;
            
         self.roadsfc         = roadsfc;
         if roadsfc:
            self.loadroads = True;
         else:
            self.loadroads = False;
            
         self.ssurgofc        = ssurgofc;
         if ssurgofc:
            self.loadssurgo = True;
         else:
            self.loadssurgo = False;

         self.vectorbuffer    = vectorbuffer;
         
         self.username        = getpass.getuser();
         self.datecreated     = datetime.datetime.now();
         self.notes           = notes;

      if cf is None:
         cf = util.fetchConfig();
         
      self.out             = cf['aoistorage'];
      self.outfc           = self.out + os.sep + util.g_aoi_fc;

      self.outslope        = self.aoi_id + '_SLOPE';
      self.outlandcover    = self.aoi_id + '_LANDCOVER';
      self.outnhd          = self.aoi_id + '_NHD';
      self.outroads        = self.aoi_id + '_ROADS';
      self.outssurgo       = self.aoi_id + '_SSURGO';

   #...........................................................................
   def unzipSample(self):

      util.dzlog(".  Unzipping sample.",arcmsg=True);

      if not os.path.exists(self.zipfile):
         msg = "Sample zip file not found [" + self.zipfile + "]";
         util.dzlog(msg,'error');
         raise arcpy.ExecuteError(msg);

      with zipfile.ZipFile(self.zipfile,'r') as zip_ref:
         zip_ref.extractall(util.g_temp);

      if not os.path.exists(self.fgdb):
         msg = "Sample fgdb [" + self.fgdb + "] not found in zipfile [" + self.zipfile + "]";
         util.dzlog(msg,'error');
         raise arcpy.ExecuteError(msg);

   #...........................................................................
   def loadSample(self):

      util.dzlog(".  Loading sample.",arcmsg=True);
      workspace = arcpy.env.workspace;

      ##........................................................................##
      if not os.path.exists(self.fgdb):
         msg = "Sample fgdb [" + item['fileGDB'] + "] not found.";
         util.dzlog(msg,'error');
         raise arcpy.ExecuteError(msg);

      if not arcpy.Exists(self.outfc):
         msg = "AOIs feature class not found in aoi storage gdb.";
         util.dzlog(msg,'error');
         raise arcpy.ExecuteError(msg);

      ##........................................................................##
      if arcpy.Exists(self.out + os.sep + self.outslope):
         arcpy.Delete_management(self.out + os.sep + self.outslope);

      if arcpy.Exists(self.out + os.sep + self.outlandcover):
         arcpy.Delete_management(self.out + os.sep + self.outlandcover);

      if arcpy.Exists(self.out + os.sep + self.outnhd):
         arcpy.Delete_management(self.out + os.sep + self.outnhd);

      if arcpy.Exists(self.out + os.sep + self.outroads):
         arcpy.Delete_management(self.out + os.sep + self.outroads);

      if arcpy.Exists(self.out + os.sep + self.outssurgo):
         arcpy.Delete_management(self.out + os.sep + self.outssurgo);

      with arcpy.da.UpdateCursor(self.outfc,"aoi_id") as cursor:
         for row in cursor:
            if row[0] == self.aoi_id:
               cursor.deleteRow();

      ##........................................................................##
      if self.loadslope:
         ret = arcpy.GetRasterProperties_management(
             in_raster     = self.fgdb + os.sep + self.sloperaster
            ,property_type = "CELLSIZEX"
         );
         slopegridsize = ret.getOutput(0);

         arcpy.Copy_management(
             in_data  = self.fgdb + os.sep + self.sloperaster
            ,out_data = self.out + os.sep + self.outslope
         );
      else:
         self.outslope = None;
         slopegridsize = None;

      ##........................................................................##
      if self.loadlandcover:
         ret = arcpy.GetRasterProperties_management(
             in_raster     = self.fgdb + os.sep + self.landcoverraster
            ,property_type = "CELLSIZEX"
         );
         landcovergridsize = ret.getOutput(0);

         arcpy.Copy_management(
             in_data  = self.fgdb + os.sep + self.landcoverraster
            ,out_data = self.out + os.sep + self.outlandcover
         );
      else:
         self.outlandcover = None;
         landcovergridsize = None;

      ##........................................................................##
      if self.loadnhd:
         util.emptyNHD(
             workspace = self.out
            ,fcname    = self.outnhd
         );

         arcpy.Append_management(
             inputs      = self.fgdb + os.sep + self.nhdfc
            ,target      = self.out + os.sep + self.outnhd
            ,schema_type = 'NO_TEST'
         );

      else:
         self.outnhd = None;

      if self.loadroads:
         util.emptyRoads(
             workspace = self.out
            ,fcname    = self.outroads
         );

         arcpy.Append_management(
             inputs      = self.fgdb + os.sep + self.roadsfc
            ,target      = self.out + os.sep + self.outroads
            ,schema_type = 'NO_TEST'
         );

      else:
         self.outroads = None;

      if self.loadssurgo:
         util.emptySSURGO(
             workspace = self.out
            ,fcname    = self.outssurgo
         );

         arcpy.Append_management(
             inputs      = self.fgdb + os.sep + self.ssurgofc
            ,target      = self.out + os.sep + self.outssurgo
            ,schema_type = 'NO_TEST'
         );

      else:
         self.outssurgo = None;

      ##........................................................................##
      with arcpy.da.SearchCursor(self.fgdb + os.sep + self.aoifc,"shape@") as cursor:
         for row in cursor:
            aoishape = row[0];

      flds = [
          'aoi_id'
         ,'sloperaster'
         ,'sloperastersource'
         ,'slopegridsize'
         ,'landcoverraster'
         ,'landcoverrastersource'
         ,'landcovergridsize'
         ,'nhdfc'
         ,'nhdfcsource'
         ,'roadsfc'
         ,'roadsfcsource'
         ,'ssurgofc'
         ,'ssurgofcsource'
         ,'vectorbuffer'
         ,'username'
         ,'datecreated'
         ,'notes'
         ,'shape@'
      ];
      with arcpy.da.InsertCursor(self.outfc,flds) as cursor:
         cursor.insertRow((
             self.aoi_id
            ,self.outslope
            ,None
            ,slopegridsize
            ,self.outlandcover
            ,None
            ,landcovergridsize
            ,self.outnhd
            ,None
            ,self.outroads
            ,None
            ,self.outssurgo
            ,None
            ,self.vectorbuffer
            ,self.username
            ,self.datecreated
            ,self.notes
            ,aoishape
         ));

      ##........................................................................##
      arcpy.Delete_management(self.fgdb);

   #...........................................................................
   def loadAOI(self):

      util.dzlog(".  Loading new area of interest.",arcmsg=True);
      workspace = arcpy.env.workspace;

      ##........................................................................##
      if not arcpy.Exists(self.outfc):
         msg = "AOIs feature class not found in aoi storage gdb.";
         util.dzlog(msg,'error');
         raise arcpy.ExecuteError(msg);

      ##........................................................................##
      if arcpy.Exists(self.out + os.sep + self.outslope):
         arcpy.Delete_management(self.out + os.sep + self.outslope);

      if arcpy.Exists(self.out + os.sep + self.outlandcover):
         arcpy.Delete_management(self.out + os.sep + self.outlandcover);

      if arcpy.Exists(self.out + os.sep + self.outnhd):
         arcpy.Delete_management(self.out + os.sep + self.outnhd);

      if arcpy.Exists(self.out + os.sep + self.outroads):
         arcpy.Delete_management(self.out + os.sep + self.outroads);

      if arcpy.Exists(self.out + os.sep + self.outssurgo):
         arcpy.Delete_management(self.out + os.sep + self.outssurgo);

      with arcpy.da.UpdateCursor(self.outfc,"aoi_id") as cursor:
         for row in cursor:
            if row[0] == self.aoi_id:
               cursor.deleteRow();
               
      ##---------------------------------------------------------------------##
      # Decide whether to utilize the memory workspace or the scratch workspace
      d = arcpy.GetInstallInfo();
      
      if d['Version'][:3] == '2.3':
         wrkGDB = arcpy.env.scratchGDB;
         
      else:
         wrkGDB = 'memory';
               
      ##........................................................................##
      if self.loadnhd or self.loadroads or self.loadssurgo:
         arcpy.AddMessage(".  Generating AOI buffer...");
         
         if arcpy.Exists(wrkGDB + os.sep + "aoi"):
            arcpy.Delete_management(wrkGDB + os.sep + "aoi");
            
         if arcpy.Exists(wrkGDB + os.sep + "aoibuffer"):
            arcpy.Delete_management(wrkGDB + os.sep + "aoibuffer");
         
         if self.vectorbuffer == 0:
         
            arcpy.CopyFeatures_management(
                in_features       = self.aoifc
               ,out_feature_class = wrkGDB + os.sep + "aoibuffer"
            );
         
         else:
         
            arcpy.CopyFeatures_management(
                in_features       = self.aoifc
               ,out_feature_class = wrkGDB + os.sep + "aoi"
            );
            
            arcpy.Buffer_analysis(
                in_features              = wrkGDB + os.sep + "aoi"
               ,out_feature_class        = wrkGDB + os.sep + "aoibuffer"
               ,buffer_distance_or_field = str(self.vectorbuffer) + " Kilometers"
            
            );

      ##........................................................................##
      if self.loadslope:
         arcpy.AddMessage(".  Clipping slope raster...");

         ret = arcpy.GetRasterProperties_management(
             in_raster     = self.sloperaster
            ,property_type = "CELLSIZEX"
         );
         slopegridsize = ret.getOutput(0);

         arcpy.Clip_management(
             in_raster           = self.sloperaster
            ,rectangle           = "#"
            ,out_raster          = self.out + os.sep + self.outslope
            ,in_template_dataset = self.aoifc
            ,clipping_geometry   = "ClippingGeometry"
         );

      else:
         slopegridsize = None;

      ##........................................................................##
      if self.loadlandcover:
         arcpy.AddMessage(".  Clipping land cover raster...");

         ret = arcpy.GetRasterProperties_management(
             in_raster     = self.landcoverraster
            ,property_type = "CELLSIZEX"
         );
         landcovergridsize = ret.getOutput(0);

         arcpy.Clip_management(
             in_raster           = self.landcoverraster
            ,rectangle           = "#"
            ,out_raster          = self.out + os.sep + self.outlandcover
            ,in_template_dataset = self.aoifc
            ,clipping_geometry   = "ClippingGeometry"
         );

      else:
         landcovergridsize = None;

      ##........................................................................##
      if self.loadnhd:
         arcpy.AddMessage(".  Clipping nhd fc...");

         arcpy.Clip_analysis(
             in_features       = self.nhdfc
            ,clip_features     = wrkGDB + os.sep + "aoibuffer"
            ,out_feature_class = wrkGDB + os.sep + "inMemoryNHD"
         );

         util.emptyNHD(
             workspace = self.out
            ,fcname    = self.outnhd
         );

         arcpy.Append_management(
             inputs      = wrkGDB + os.sep + "inMemoryNHD"
            ,target      = self.out + os.sep + self.outnhd
            ,schema_type = 'NO_TEST'
         );

         arcpy.Delete_management(wrkGDB + os.sep + "inMemoryNHD");

      ##........................................................................##
      if self.loadroads:
         arcpy.AddMessage(".  Clipping roads fc...");

         arcpy.Clip_analysis(
             in_features       = self.roadsfc
            ,clip_features     = wrkGDB + os.sep + "aoibuffer"
            ,out_feature_class = wrkGDB + os.sep + "inMemoryRoads"
         );

         util.emptyRoads(
             workspace = self.out
            ,fcname    = self.outroads
         );

         arcpy.Append_management(
             inputs      = wrkGDB + os.sep + "inMemoryRoads"
            ,target      = self.out + os.sep + self.outroads
            ,schema_type = 'NO_TEST'
         );
         
         arcpy.Delete_management(wrkGDB + os.sep + "inMemoryRoads");

      ##........................................................................##
      if self.loadssurgo:
         arcpy.AddMessage(".  Clipping ssurgo fc...");

         arcpy.Clip_analysis(
             in_features       = self.ssurgofc
            ,clip_features     = wrkGDB + os.sep + "aoibuffer"
            ,out_feature_class = wrkGDB + os.sep + "inMemorySSURGO"
         );

         util.emptySSURGO(
             workspace = self.out
            ,fcname    = self.outssurgo
         );

         arcpy.Append_management(
             inputs      = wrkGDB + os.sep + "inMemorySSURGO"
            ,target      = self.out + os.sep + self.outssurgo
            ,schema_type = 'NO_TEST'
         );
         
         arcpy.CalculateField_management(
             in_table        = self.out + os.sep + self.outssurgo
            ,field           = "hydgrpdcd"
            ,expression      = "myCalc(!hydgrpdcd!)"
            ,expression_type = "PYTHON3"
            ,code_block      = """
def myCalc(value):
   if value == None:
      return ' '
   else:
      return value
"""
         );
         
         arcpy.Delete_management(wrkGDB + os.sep + "inMemorySSURGO");

      ##........................................................................##
      with arcpy.da.SearchCursor(
          in_table    = self.aoifc
         ,field_names = "shape@"
      ) as cursor:
         for row in cursor:
            aoishape = row[0];

      flds = [
          'aoi_id'
         ,'sloperaster'
         ,'sloperastersource'
         ,'slopegridsize'
         ,'landcoverraster'
         ,'landcoverrastersource'
         ,'landcovergridsize'
         ,'nhdfc'
         ,'nhdfcsource'
         ,'roadsfc'
         ,'roadsfcsource'
         ,'ssurgofc'
         ,'ssurgofcsource'
         ,'vectorbuffer'
         ,'username'
         ,'datecreated'
         ,'notes'
         ,'shape@'
      ];
      with arcpy.da.InsertCursor(
          in_table    = self.outfc
         ,field_names = flds
      ) as cursor:
         cursor.insertRow((
             self.aoi_id
            ,self.outslope
            ,self.sloperaster
            ,slopegridsize
            ,self.outlandcover
            ,self.landcoverraster
            ,landcovergridsize
            ,self.outnhd
            ,self.nhdfc
            ,self.outroads
            ,self.roadsfc
            ,self.outssurgo
            ,self.ssurgofc
            ,self.vectorbuffer
            ,self.username
            ,self.datecreated
            ,self.notes
            ,aoishape
         ));

###############################################################################
class Scenario(object):

   flds = [
       'scenario_id'
      ,'analysis_complete'
      ,'aoi_id'
      ,'load_slope'
      ,'load_landcover'
      ,'load_nhd'
      ,'load_roads'
      ,'load_ssurgo'
      ,'slopegridsize'
      ,'landcovergridsize'
      ,'nhdgridsize'
      ,'roadsgridsize'
      ,'ssurgogridsize'
      ,'username'
      ,'datecreated'
      ,'notes'
      ,'shape@'
   ];

   #...........................................................................
   def __init__(self
      ,scenario_id
      ,cf=None
      ,aprx=None
   ):
      self.scenario_id    = scenario_id;
      self.cf             = cf;
      self.aprx           = aprx;

      if self.cf is None:
         self.cf = util.fetchConfig();

      if self.aprx is None:
         self.aprx = arcpy.mp.ArcGISProject(util.g_prj);

   #...........................................................................
   def load(self
       ,aoi_id
       ,load_slope
       ,load_landcover
       ,load_nhd
       ,nhdgridsize
       ,load_roads
       ,roadsgridsize
       ,load_ssurgo
       ,ssurgogridsize
       ,username=None
       ,datecreated=None
       ,notes=None
       ,cf=None
       ,aprx=None
   ):
      self.aoi_id            = aoi_id;
      self.analysis_complete = 'N';
      self.load_slope        = load_slope;
      self.load_landcover    = load_landcover;
      self.load_nhd          = load_nhd;
      self.nhdgridsize       = nhdgridsize;
      self.load_roads        = load_roads;
      self.roadsgridsize     = roadsgridsize;
      self.load_ssurgo       = load_ssurgo;
      self.ssurgogridsize    = ssurgogridsize;

      if cf is not None:
         self.cf          = cf;
      if aprx is not None:
         self.aprx        = aprx;

      if self.cf is None:
         self.cf = util.fetchConfig();
      if self.aprx is None:
         self.aprx = arcpy.mp.ArcGISProject(util.g_prj);

      self.username    = username;
      self.datecreated = datecreated;
      self.notes       = notes;
      if self.username is None:
         self.username = getpass.getuser();
      if self.datecreated is None:
         self.datecreated = datetime.datetime.now();
         
      ##---------------------------------------------------------------------##
      # Decide whether to utilize the memory workspace or the scratch workspace
      d = arcpy.GetInstallInfo();
      
      if d['Version'][:3] == '2.3':
         wrkGDB = arcpy.env.scratchGDB;
         
      else:
         wrkGDB = 'memory';

      ##---------------------------------------------------------------------##
      if not arcpy.Exists(cf['aoistorage']):
         util.dzlog("Error, AOI Storage location not found.",arcmsg=True);
         arcpy.AddError("error");

      aoi = util.fetchAOIbyID(
          id = self.aoi_id
         ,cf = self.cf
      );

      if aoi is None:
         util.dzlog("Error, AOI ID " + self.aoi_id + " not found in AOI Storage.",arcmsg=True);
         arcpy.AddError("error");

      if 'slopegridsize' in aoi:
         self.slopegridsize = aoi['slopegridsize'];
      else:
         self.slopegridsize = None;

      if 'landcovergridsize' in aoi:
         self.landcovergridsize = aoi['landcovergridsize'];
      else:
         self.landcovergridsize = None;
         
      if 'shape' in aoi:
         self.shape = aoi['shape'];
      else:
         self.shape = None;
         
      ##---------------------------------------------------------------------##
      if self.load_nhd or self.load_roads or self.load_ssurgo:
      
         if arcpy.Exists(wrkGDB + os.sep + "aoi"):
            arcpy.Delete_management(wrkGDB + os.sep + "aoi");
            
         # Work-around for Pro 3.4 date bugs
         
         arcpy.management.CreateFeatureclass(
             out_path      = wrkGDB
            ,out_name      = 'aoi'
            ,geometry_type = 'POLYGON'
            ,template      = cf['aoistorage'] + os.sep + util.g_aoi_fc
         );
         
         arcpy.management.Append(
             inputs     = cf['aoistorage'] + os.sep + util.g_aoi_fc
            ,target     = wrkGDB + os.sep + 'aoi'
            ,expression = "aoi_id = '" + self.aoi_id + "'"
         );
         
         #arcpy.conversion.ExportFeatures(
         #    in_features  = cf['aoistorage'] + os.sep + util.g_aoi_fc
         #   ,out_features = wrkGDB + os.sep + 'aoi'
         #   ,where_clause = "aoi_id = '" + self.aoi_id + "'"
         #);
      
      ##---------------------------------------------------------------------##
      util.deleteScenarioID(
          id   = self.scenario_id
         ,aprx = self.aprx
      );

      ##---------------------------------------------------------------------##
      self.write();

      ##---------------------------------------------------------------------##
      if self.load_slope:
         arcpy.CopyRaster_management(
             in_raster         = cf['aoistorage'] + os.sep + self.aoi_id + '_SLOPE'
            ,out_rasterdataset = self.aprx.defaultGeodatabase + os.sep + self.scenario_id + '_EXTRACT_SLOPE'
         );

      ##---------------------------------------------------------------------##
      if self.load_landcover:
         arcpy.CopyRaster_management(
             in_raster         = cf['aoistorage'] + os.sep + self.aoi_id + '_LANDCOVER'
            ,out_rasterdataset = self.aprx.defaultGeodatabase + os.sep + self.scenario_id + '_EXTRACT_LANDCOVER'
         );

      ##---------------------------------------------------------------------##
      if self.load_nhd:
         
         if arcpy.Exists(wrkGDB + os.sep + "nhdtemp"):
            arcpy.Delete_management(wrkGDB + os.sep + "nhdtemp");

         nhdEucDistance = arcpy.sa.EucDistance(
             in_source_data  = cf['aoistorage'] + os.sep + self.aoi_id + '_NHD'
            ,cell_size       = self.nhdgridsize
            ,distance_method = "GEODESIC"
         );

         nhdEucDistance.save(wrkGDB + os.sep + "nhdtemp");
         
         arcpy.Clip_management(
             in_raster           = wrkGDB + os.sep + "nhdtemp"
            ,out_raster          = self.aprx.defaultGeodatabase + os.sep + self.scenario_id + '_EXTRACT_NHD'
            ,in_template_dataset = wrkGDB + os.sep + "aoi"
            ,nodata_value        = -1
            ,clipping_geometry   = 'ClippingGeometry'
         );
         
         arcpy.Delete_management(wrkGDB + os.sep + "nhdtemp");

      ##---------------------------------------------------------------------##
      if self.load_roads:
      
         if arcpy.Exists(wrkGDB + os.sep + "roadstemp"):
            arcpy.Delete_management(wrkGDB + os.sep + "roadstemp");
      
         roadsEucDistance = arcpy.sa.EucDistance(
             in_source_data  = cf['aoistorage'] + os.sep + self.aoi_id + '_ROADS'
            ,cell_size       = self.roadsgridsize
            ,distance_method = "GEODESIC"
         );

         roadsEucDistance.save(wrkGDB + os.sep + "roadstemp");
         
         arcpy.Clip_management(
             in_raster           = wrkGDB + os.sep + "roadstemp"
            ,out_raster          = self.aprx.defaultGeodatabase + os.sep + self.scenario_id + '_EXTRACT_ROADS'
            ,in_template_dataset = wrkGDB + os.sep + "aoi"
            ,nodata_value        = -1
            ,clipping_geometry   = 'ClippingGeometry'
         );
         
         arcpy.Delete_management(wrkGDB + os.sep + "roadstemp");

      ##---------------------------------------------------------------------##
      # Note this vector buffer handling is not really needed for SSURGO polygons
      # However, if additional vector criteria analysis was added then it might 
      # well be needed.  There is no particular harm in the buffered clip so 
      # leaving it in for future flexibility.
      ##---------------------------------------------------------------------##
      if self.load_ssurgo:
      
         if arcpy.Exists(wrkGDB + os.sep + "ssurgotemp"):
            arcpy.Delete_management(wrkGDB + os.sep + "ssurgotemp");
         
         arcpy.PolygonToRaster_conversion(
             in_features       = cf['aoistorage'] + os.sep + self.aoi_id + '_SSURGO'
            ,value_field       = "hydgrpdcd"
            ,out_rasterdataset = wrkGDB + os.sep + "ssurgotemp"
            ,cell_assignment   = "CELL_CENTER"
            ,priority_field    = None
            ,cellsize          = self.ssurgogridsize
         );

         arcpy.Clip_management(
             in_raster           = wrkGDB + os.sep + "ssurgotemp"
            ,out_raster          = self.aprx.defaultGeodatabase + os.sep + self.scenario_id + '_EXTRACT_SSURGO'
            ,in_template_dataset = wrkGDB + os.sep + "aoi"
            ,nodata_value        = -1
            ,clipping_geometry   = 'ClippingGeometry'
         );
         
         arcpy.Delete_management(wrkGDB + os.sep + "ssurgotemp");
                 
   #...........................................................................
   def write(self):

      if self.load_slope:
         str_load_slope = 'Y';
      else:
         str_load_slope = 'N';
         
      if self.load_landcover:
         str_load_landcover = 'Y';
      else:
         str_load_landcover = 'N';
         
      if self.load_nhd:
         str_load_nhd = 'Y';
      else:
         str_load_nhd = 'N';
         
      if self.load_roads:
         str_load_roads = 'Y';
      else:
         str_load_roads = 'N';
         
      if self.load_ssurgo:
         str_load_ssurgo = 'Y';
      else:
         str_load_ssurgo = 'N';
      
      boo_exists = False;

      ##........................................................................##
      with arcpy.da.SearchCursor(
          in_table    = self.aprx.defaultGeodatabase + os.sep + util.g_scenario_fc
         ,field_names = "scenario_id"
      ) as cursor:
         for row in cursor:
            if row[0] == self.scenario_id:
               boo_exists = True;

      ##........................................................................##
      if boo_exists:
         with arcpy.da.UpdateCursor(
             in_table    = self.aprx.defaultGeodatabase + os.sep + util.g_scenario_fc
            ,field_names = self.flds
         ) as cursor:
            for row in cursor:
               if row[0] == self.scenario_id:
                  row[1]  = self.analysis_complete
                  row[2]  = self.aoi_id;
                  row[3]  = str_load_slope;
                  row[4]  = str_load_landcover;
                  row[5]  = str_load_nhd;
                  row[6]  = str_load_roads;
                  row[7]  = str_load_ssurgo;
                  row[8]  = self.slopegridsize;
                  row[9]  = self.landcovergridsize;
                  row[10] = self.nhdgridsize;
                  row[11] = self.roadsgridsize;
                  row[12] = self.ssurgogridsize;
                  row[13] = self.username;
                  row[14] = self.datecreated;
                  row[15] = self.notes;
                  row[16] = self.shape;
                  cursor.updateRow(row);
                  break;

      else:
         with arcpy.da.InsertCursor(
             in_table    = self.aprx.defaultGeodatabase + os.sep + util.g_scenario_fc
            ,field_names = self.flds
         ) as cursor:
            cursor.insertRow((
                self.scenario_id
               ,self.analysis_complete
               ,self.aoi_id
               ,str_load_slope
               ,str_load_landcover
               ,str_load_nhd
               ,str_load_roads
               ,str_load_ssurgo
               ,self.slopegridsize
               ,self.landcovergridsize
               ,self.nhdgridsize
               ,self.roadsgridsize
               ,self.ssurgogridsize
               ,self.username
               ,self.datecreated
               ,self.notes
               ,self.shape
            ));
