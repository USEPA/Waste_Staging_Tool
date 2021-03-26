import arcpy;
import os,sys;
import logging,inspect;
import tempfile,json;
import datetime,re,difflib;

g_prj                      = "CURRENT";
g_logging                  = logging.DEBUG;
g_temp                     = tempfile.gettempdir();
g_pn                       = os.path.dirname(os.path.realpath(__file__));
g_srid                     = 102010;
g_aoi_gdb                  = 'AreaOfInterestStorage.gdb';
g_aoi_fc                   = 'AOIs';
g_default_nhdgridsize      = 250;
g_default_tnmroadsgridsize = 250;
g_default_ssurgogridsize   = 250;
g_scenario_fc              = "Scenarios";
g_stash_tbl                = "Stash";
g_default_slope_reclassification     = "Value > 10";
g_default_landcover_reclassification = "Value = 11 OR Value = 23 OR Value = 24 OR Value = 41 OR Value = 42 OR Value = 43 OR Value = 81 OR Value = 82 OR Value = 90 OR Value = 95";
g_default_nhd_reclassification       = "Value <= 500";
g_default_roads_reclassification     = "Value < 200 OR Value > 500";
g_default_ssurgo_reclassification    = "hydgrpdcd = 'B' OR hydgrpdcd = 'B/D' OR hydgrpdcd = 'A' OR hydgrpdcd = 'A/D' OR hydgrpdcd = ' '";

###############################################################################
def addField(in_table,field_name,field_type,field_alias,field_is_nullable):

   desc = arcpy.Describe(in_table);

   flds = desc.fields;
   boo_exists = False;

   for fld in flds:
      if fld.name.lower() == field_name.lower():
         boo_exists = True;

   if not boo_exists:

      arcpy.AddField_management(
          in_table
         ,field_name
         ,field_type
         ,field_alias=field_alias
         ,field_is_nullable=field_is_nullable
      );

###############################################################################
def addFieldCalc(in_table,field_name,field_type,field_alias,field_is_nullable,calc_value):

   desc = arcpy.Describe(in_table);

   flds = desc.fields;
   boo_exists = False;

   for fld in flds:
      if fld.name.lower() == field_name.lower():
         boo_exists = True;

   if not boo_exists:

      arcpy.AddField_management(
          in_table
         ,field_name
         ,field_type
         ,field_alias=field_alias
         ,field_is_nullable=field_is_nullable
      );

   arcpy.CalculateField_management(
       in_table
      ,field_name
      ,calc_value
      ,"PYTHON3"
   );
   
###############################################################################
def checkScenarioSystem(aprx=None):

   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);
      
   if not arcpy.Exists(aprx.defaultGeodatabase + os.sep + g_scenario_fc):
      return False;
      
   return True;

###############################################################################
def fetchScenarioIDs(aprx=None):

   rez = [];
   def_scenario = None;

   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);
      
   if aprx.activeMap is not None:
      amap = aprx.activeMap.name;
   else:
      amap = None;
      
   if not checkScenarioSystem(aprx=aprx):
      msg = "Scenario table not found";
      dzlog(msg,'warning');
      return (rez,None);

   ##........................................................................##
   with arcpy.da.SearchCursor(aprx.defaultGeodatabase + os.sep + g_scenario_fc,"scenario_id") as cursor:
      for row in cursor:
         if row[0] is not None and row[0] != "":
            rez.append(row[0]);
         
   if len(rez) == 1:
      def_scenario = rez[0];
      
   elif len(rez) > 0 and amap is not None:
      close = difflib.get_close_matches(amap,rez);
      
      if close is None or len(close) == 0:
         stash = read_stash();
         
         if 'scenario_id' in stash:
            
            if stash['scenario_id'] in rez:
               def_scenario = stash['scenario_id'];
               
            else:
               def_scenario = None;
      
      else:
         def_scenario = close[0];
         
   elif len(rez) > 0:
      def_scenario = rez[0];
      
   if def_scenario is None and rez is not None and len(rez) > 0:
      def_scenario = rez[0];

   return (sorted(rez),def_scenario);
   
###############################################################################
def fetchMapNames(aprx=None):

   rez = [];

   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);

   map_objs = aprx.listMaps('*');
   for item in map_objs:
      rez.append(item.name);
   
   if len(rez) > 0:
      if aprx.activeMap is not None:
         def_mapname = aprx.activeMap.name;
      else:
         def_mapname = None;
   else:
      def_mapname = None;

   return (sorted(rez),def_mapname);
   
###############################################################################
def fetchWeightedSumLayer(aprx=None):

   rez = None;
   
   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);

   if aprx.activeMap is not None:
      layer_objs = aprx.activeMap.listLayers('*');
   else:
      return None;
   
   if len(layer_objs) > 0:
      regex = re.compile('.*weightedsum.*');
      
      for item in layer_objs:
         if re.match(regex,item.name.lower()):
            rez = item.name;
            break;

   return rez;
   
###############################################################################
def fetchReclassification(scenarioid,aprx=None):

   slopeenabled              = True;
   slopereclassification     = g_default_slope_reclassification;
   landcoverenabled          = True;
   landcoverreclassification = g_default_landcover_reclassification;
   nhdenabled                = True;
   nhdreclassification       = g_default_nhd_reclassification;
   roadsenabled              = True;
   roadsreclassification     = g_default_roads_reclassification;
   ssurgoenabled             = True;
   ssurgoreclassification    = g_default_ssurgo_reclassification;
   
   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);
      
   fc = aprx.defaultGeodatabase + os.sep + g_scenario_fc
   if not arcpy.Exists(fc):
      msg = "Scenario table not found";
      dzlog(msg,'warning');
      return (
          None
         ,None
         ,None
         ,None
         ,None
         ,None
         ,None
         ,None
         ,None
         ,None
      );
      
   
   ##........................................................................##
   with arcpy.da.SearchCursor(
       fc
      ,[
          "scenario_id"
         ,"load_slope"
         ,"load_landcover"
         ,"load_nhd"
         ,"load_roads"
         ,"load_ssurgo"
         ,"slopegridsize"
         ,"slopereclassification"
         ,"landcovergridsize"
         ,"landcoverreclassification"
         ,"nhdgridsize"
         ,"nhdreclassification"
         ,"roadsgridsize"
         ,"roadsreclassification"
         ,"ssurgogridsize"
         ,"ssurgoreclassification"
      ]
   ) as cursor:
      for row in cursor:
         if row[0] == scenarioid:
            
            if row[1] == 'N':
               slopeenabled = False;
               slopereclassification = None;
            else:
               if row[6] is not None and row[6] != "":
                  if row[7] is not None and row[7] != "":
                     slopereclassification = row[7];
               else:
                  slopeenabled = False;
      
            if row[2] == 'N':
               landcoverenabled = False;
               landcoverreclassification = None;
            else:
               if row[8] is not None and row[8] != "":
                  if row[9] is not None and row[9] != "":
                     landcoverreclassification = row[9];
               else:
                  landcoverenabled = False;
               
            if row[3] == 'N':
               nhdenabled = False;
               nhdreclassification = None;
            else:
               if row[10] is not None and row[10] != "":
                  if row[11] is not None and row[11] != "":
                     nhdreclassification = row[11];
               else:
                  nhdenabled = False;
               
            if row[4] == 'N':
               roadsenabled = False;
               roadsreclassification = None;
            else:
               if row[12] is not None and row[12] != "":
                  if row[13] is not None and row[13] != "":
                     roadsreclassification = row[13];
               else:
                  roadsenabled = False;
               
            if row[5] == 'N':
               ssurgoenabled = False;
               ssurgoreclassification = None;
            else:
               if row[14] is not None and row[14] != "":
                  if row[15] is not None and row[15] != "":
                     ssurgoreclassification = row[15];
               else:
                  ssurgoenabled = False;
               
            break;   
   
   if slopereclassification == 'None':
      slopereclassification = None;
   if landcoverreclassification == 'None':
      landcoverreclassification = None;
   if nhdreclassification == 'None':
      nhdreclassification = None;
   if roadsreclassification == 'None':
      roadsreclassification = None;
   if ssurgoreclassification == 'None':
      ssurgoreclassification = None;
   
   return (
       slopeenabled
      ,slopereclassification
      ,landcoverenabled
      ,landcoverreclassification
      ,nhdenabled
      ,nhdreclassification
      ,roadsenabled
      ,roadsreclassification
      ,ssurgoenabled
      ,ssurgoreclassification
   );
   
###############################################################################
def fetchWeights(scenarioid,aprx=None):

   slopeenabled     = True;
   slopeweight      = "1";
   landcoverenabled = True;
   landcoverweight  = "1";
   nhdenabled       = True;
   nhdweight        = "1";
   roadsenabled     = True;
   roadsweight      = "1";
   ssurgoenabled    = True;
   ssurgoweight     = "1";
   
   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);
      
   fc = aprx.defaultGeodatabase + os.sep + g_scenario_fc
   if not arcpy.Exists(fc):
      msg = "Scenario table not found";
      dzlog(msg,'warning');
      return (
          None
         ,None
         ,None
         ,None
         ,None
         ,None
         ,None
         ,None
         ,None
         ,None
      );
      
   
   ##........................................................................##
   with arcpy.da.SearchCursor(
       fc
      ,[
          "scenario_id"
         ,"load_slope"
         ,"load_landcover"
         ,"load_nhd"
         ,"load_roads"
         ,"load_ssurgo"
         ,"slopegridsize"
         ,"slopeweight"
         ,"landcovergridsize"
         ,"landcoverweight"
         ,"nhdgridsize"
         ,"nhdweight"
         ,"roadsgridsize"
         ,"roadsweight"
         ,"ssurgogridsize"
         ,"ssurgoweight"
      ]
   ) as cursor:
      for row in cursor:
         if row[0] == scenarioid:
            
            if row[1] == 'N':
               slopeenabled = False;
               slopeweight = None;
            else:
               if row[6] is not None and row[6] != "":
                  if row[7] is not None and row[7] != "":
                     slopeweight = row[7];
               else:
                  slopeenabled = False;
            
            if row[2] == 'N':
               landcoverenabled = False;
               landcoverweight = None;
            else:
               if row[8] is not None and row[8] != "":
                  if row[9] is not None and row[9] != "":
                     landcoverweight = row[9];
               else:
                  landcoverenabled = False;
               
            if row[3] == 'N':
               nhdenabled = False;
               nhdweight = None;
            else:
               if row[10] is not None and row[10] != "":
                  if row[11] is not None and row[11] != "":
                     nhdweight = row[11];
               else:
                  nhdenabled = False;
               
            if row[4] == 'N':
               roadsenabled = False;
               roadsweight = None;
            else:
               if row[12] is not None and row[12] != "":
                  if row[13] is not None and row[13] != "":
                     roadsweight = row[13];
               else:
                  roadsenabled = False;
               
            if row[5] == 'N':
               ssurgoenabled = False;
               ssurgoweight = None;
            else:
               if row[14] is not None and row[14] != "":
                  if row[15] is not None and row[15] != "":
                     ssurgoweight = row[15];
               else:
                  ssurgoenabled = False;
            
            break;
   
   if slopeweight == 'None':
      slopeweight = None;
   if landcoverweight == 'None':
      landcoverweight = None;
   if nhdweight == 'None':
      nhdweight = None;
   if roadsweight == 'None':
      roadsweight = None;
   if ssurgoweight == 'None':
      ssurgoweight = None;
      
   return (
       slopeenabled
      ,slopeweight
      ,landcoverenabled
      ,landcoverweight
      ,nhdenabled
      ,nhdweight
      ,roadsenabled
      ,roadsweight
      ,ssurgoenabled
      ,ssurgoweight
   );

###############################################################################
def tempLyrx(in_layerfile,dataset,name=None,aprx=None):

   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);

   with open(in_layerfile,"r") as jsonFile_target:
      data_in = json.load(jsonFile_target);

   for item in data_in["layerDefinitions"]:
      if item["name"] == "WeightedSum" or item["name"] == "StagingSiteSelection":
         item["featureTable"]["dataConnection"]["workspaceConnectionString"] = "DATABASE=" + aprx.defaultGeodatabase;
         item["featureTable"]["dataConnection"]["dataset"] = dataset;

         if name is not None:
            item["name"] = name;

   lyrx_target = arcpy.env.scratchFolder + os.sep + dataset + '.lyrx';
   with open(lyrx_target,"w") as jsonFile:
      json.dump(data_in,jsonFile);

   return lyrx_target;

###############################################################################
def dzlog(msg,lvl='info',force=False,reset=False,arcmsg=False):

   lfmat   = '%(asctime)-15s: %(message)s ';
   callerframerecord = inspect.stack()[1];
   frame   = callerframerecord[0];
   info    = inspect.getframeinfo(frame);
   msg_log = msg + ": " + info.function + ": " + str(info.lineno);
   
   ##........................................................................##
   if arcmsg:
      arcpy.AddMessage(msg);

   ##........................................................................##
   if reset:

      while len(logging.root.handlers) > 0:
         logging.root.removeHandler(logging.root.handlers[-1]);

   ##........................................................................##
   if len(logging.root.handlers) == 0 or reset:

      logging.basicConfig(
          filename = g_pn + os.sep + 'toolbox.log'
         ,format   = lfmat
         ,level    = g_logging
      );

   ##........................................................................##
   if force:

      if lvl == 'debug':
         level = logging.DEBUG;

      elif lvl == 'info':
         level = logging.INFO;

      elif lvl == 'warning':
         level = logging.WARNING;

      elif lvl == 'error':
         level = logging.ERROR;

      elif lvl == 'critical':
         level = logging.CRITICAL;

      if not logging.getLogger().isEnabledFor(level):

         while len(logging.root.handlers) > 0:
            logging.root.removeHandler(logging.root.handlers[-1]);

         logging.basicConfig(
             filename = g_pn + os.sep + 'toolbox.log'
            ,format   = lfmat
            ,level    = level
         );
   
   ##........................................................................##
   if lvl == 'debug':
      logging.debug(msg_log);

   elif lvl == 'info':
      logging.info(msg_log);

   elif lvl == 'warning':
      logging.warning(msg_log);

   elif lvl == 'error':
      logging.error(msg_log);

   elif lvl == 'critical':
      logging.critical(msg_log);
      
###############################################################################
def checkAOISystem(cf=None):

   if cf is None:
      cf = fetchConfig();

   if not arcpy.Exists(cf['aoistorage'] + os.sep + g_aoi_fc):
      return False;
      
   return True;
      
###############################################################################
def fetchAOIIDs(cf=None):

   rez = [];

   if cf is None:
      cf = fetchConfig();

   if not checkAOISystem(cf=None):
      dzlog("AOIs project table not found",'ERROR');
      return rez;

   ##........................................................................##
   try:
      with arcpy.da.SearchCursor(
          cf['aoistorage'] + os.sep + g_aoi_fc
         ,"aoi_id"
      ) as cursor:
         for row in cursor:
            if row[0] is not None and row[0] != "" and row[0] != " ":
               rez.append(row[0]);
            
   except Exception as e:
      dzlog(str(sys.exc_info()),'ERROR');
      raise;

   return sorted(rez);

###############################################################################
def fetchAOIbyID(id,cf=None):

   rez = {};

   if cf is None:
      cf = fetchConfig();

   if not arcpy.Exists(cf['aoistorage'] + os.sep + g_aoi_fc):
      msg = "AOIs project table not found";
      dzlog(msg,'warning');
      return rez;

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
      ,'username'
      ,'datecreated'
      ,'notes'
      ,'shape@'
   ];

   ##........................................................................##
   with arcpy.da.SearchCursor(cf['aoistorage'] + os.sep + g_aoi_fc,flds) as cursor:
      for row in cursor:
         if row[0] == id:
            rez['aoi_id']                = row[0];
            rez['sloperaster']           = row[1];
            rez['sloperastersource']     = row[2];
            rez['slopegridsize']         = row[3];
            rez['landcoverraster']       = row[4];
            rez['landcoverrastersource'] = row[5];
            rez['landcovergridsize']     = row[6];
            rez['nhdfc']                 = row[7];
            rez['nhdfcsource']           = row[8];
            rez['roadsfc']               = row[9];
            rez['roadsfcsource']         = row[10];
            rez['ssurgofc']              = row[11];
            rez['ssurgofcsource']        = row[12];
            rez['username']              = row[13];
            rez['datecreated']           = row[14];
            rez['notes']                 = row[15];
            rez['shape']                 = row[16];

            return rez;

   return None;

###############################################################################
def deleteAOIFiles(aoi_id,cf=None):

   if cf is None:
      cf = fetchConfig();

   if arcpy.Exists(cf['aoistorage'] + os.sep + aoi_id + "_SLOPE"):
      arcpy.Delete_management(cf['aoistorage'] + os.sep + aoi_id + "_SLOPE");
   if arcpy.Exists(cf['aoistorage'] + os.sep + aoi_id + "_LANDCOVER"):
      arcpy.Delete_management(cf['aoistorage'] + os.sep + aoi_id + "_LANDCOVER");
   if arcpy.Exists(cf['aoistorage'] + os.sep + aoi_id + "_NHD"):
      arcpy.Delete_management(cf['aoistorage'] + os.sep + aoi_id + "_NHD");
   if arcpy.Exists(cf['aoistorage'] + os.sep+ aoi_id + "_ROADS"):
      arcpy.Delete_management(cf['aoistorage'] + os.sep + aoi_id + "_ROADS");
   if arcpy.Exists(cf['aoistorage'] + os.sep + aoi_id + "_SSURGO"):
      arcpy.Delete_management(cf['aoistorage'] + os.sep + aoi_id + "_SSURGO");

###############################################################################
def scenarioIDExists(id,aprx=None):

   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);

   boo_hit = False;
   
   with arcpy.da.SearchCursor(
       in_table    = aprx.defaultGeodatabase + os.sep + g_scenario_fc
      ,field_names = "scenario_id"
   ) as cursor:
      for row in cursor:
         if row[0] == id:
            boo_hit = True;
            break;
            
   return boo_hit;
   
###############################################################################
def deleteScenarioID(id,aprx=None):

   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);

   boo_hit = False;

   ##........................................................................##
   with arcpy.da.UpdateCursor(aprx.defaultGeodatabase + os.sep + g_scenario_fc,"scenario_id") as cursor:
      for row in cursor:
         if row[0] == id:
            cursor.deleteRow();
            boo_hit = True;
            break;

   if boo_hit:
      deleteScenarioFiles(id,aprx=aprx);

###############################################################################
def deleteScenarioFiles(id,aprx=None):

   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);

   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_EXTRACT_SLOPE"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_EXTRACT_SLOPE");
   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_EXTRACT_LANDCOVER"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_EXTRACT_LANDCOVER");
   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_EXTRACT_NHD"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_EXTRACT_NHD");
   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_EXTRACT_ROADS"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_EXTRACT_ROADS");
   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_EXTRACT_SSURGO"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_EXTRACT_SSURGO");

   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_RECLASS_SLOPE"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_RECLASS_SLOPE");
   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_RECLASS_LANDCOVER"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_RECLASS_LANDCOVER");
   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_RECLASS_NHD"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_RECLASS_NHD");
   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_RECLASS_ROADS"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_RECLASS_ROADS");
   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_RECLASS_SSURGO"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_RECLASS_SSURGO");

   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_WEIGHTEDSUM"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_WEIGHTEDSUM");
   if arcpy.Exists(aprx.defaultGeodatabase + os.sep + id + "_STAGINGSITESELECTION"):
      arcpy.Delete_management(aprx.defaultGeodatabase + os.sep + id + "_STAGINGSITESELECTION");

###############################################################################
def fetchConfig():

   file = g_pn + os.sep + 'config.json';

   if not os.path.exists(file):
      msg = "configuration json file not found";
      dzlog(msg,'error');
      raise arcpy.ExecuteError(msg);

   with open(file,"r") as json_f:
      
      try:
         json_d = json.load(json_f);
      
      except ValueError as e:
         msg = "Project config.json file does not contain valid JSON.";
         dzlog(msg,'error');
         raise arcpy.ExecuteError(msg);

   if 'aoistorage' not in json_d:
      json_d['aoistorage'] = 'default';

   if json_d['aoistorage'] == "default":
      json_d['aoistorage'] = g_pn + os.sep + g_aoi_gdb;

   return json_d;

###############################################################################
def updateConfig(key,value):

   file = g_pn + os.sep + 'config.json';

   if not os.path.exists(file):
      msg = "configuration json file not found";
      dzlog(msg,'error');
      raise arcpy.ExecuteError(msg);

   with open(file,"r") as json_f:
      json_d = json.load(json_f);

   json_d[key] = value;

   with open(file,"w") as json_f:
      json.dump(json_d,json_f,indent=3);

   if 'aoistorage' not in json_d:
      json_d['aoistorage'] = 'default';

   if json_d['aoistorage'] == "default":
      json_d['aoistorage'] = g_pn + os.sep + g_aoi_gdb;

   return json_d;

###############################################################################
def emptyNHD(workspace,fcname):

   arcpy.env.workspace = workspace;

   arcpy.CreateFeatureclass_management(
       out_path          = workspace
      ,out_name          = fcname
      ,geometry_type     = "POLYGON"
      ,has_m             = "DISABLED"
      ,has_z             = "DISABLED"
      ,spatial_reference = arcpy.SpatialReference(g_srid)
      ,config_keyword    = None
   );

   arcpy.management.AddFields(
       fcname
      ,[
          ['ftype'                     ,'LONG'  ,'FType'                   ,None,None,'']
         ,['fcode'                     ,'LONG'  ,'FCode'                   ,None,None,'']
       ]
   );

###############################################################################
def emptyRoads(workspace,fcname):

   arcpy.env.workspace = workspace;

   arcpy.CreateFeatureclass_management(
       out_path          = workspace
      ,out_name          = fcname
      ,geometry_type     = "POLYLINE"
      ,has_m             = "DISABLED"
      ,has_z             = "DISABLED"
      ,spatial_reference = arcpy.SpatialReference(g_srid)
      ,config_keyword    = None
   );

   arcpy.management.AddFields(
       fcname
      ,[
          ['tnmfrc'                    ,'LONG'  ,'TNMFRC'                  ,None,None,'']
         ,['mtfcc_code'                ,'TEXT'  ,'MTFCC_Code'              ,16,  None,'']
       ]
   );

###############################################################################
def emptySSURGO(workspace,fcname):

   arcpy.env.workspace = workspace;

   arcpy.CreateFeatureclass_management(
       out_path          = workspace
      ,out_name          = fcname
      ,geometry_type     = "POLYGON"
      ,has_m             = "DISABLED"
      ,has_z             = "DISABLED"
      ,spatial_reference = arcpy.SpatialReference(g_srid)
      ,config_keyword    = None
   );

   arcpy.management.AddFields(
       fcname
      ,[
          ['musym'                     ,'TEXT'  ,'Map Unit Symbol'                      ,6   ,None,'']
         ,['mukey'                     ,'TEXT'  ,'Map Unit Key'                         ,15  ,None,'']
         ,['hydgrpdcd'                 ,'TEXT'  ,'Hydrologic Group - Dominant Condition',5   ,None,'']
       ]
   );
   
###############################################################################
def fetchScenarioCharacteristics_dict(scenario_id,aprx=None):

   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);
      
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
   ];
   
   analysis_complete                 = None;
   aoi_id                            = None;
   load_slope                        = None;
   load_landcover                    = None;
   load_nhd                          = None;
   load_roads                        = None;
   load_ssurgo                       = None;
   slopegridsize                     = None;
   landcovergridsize                 = None;
   nhdgridsize                       = None;
   roadsgridsize                     = None;
   ssurgogridsize                    = None;
   slopereclassification             = None;
   landcoverreclassification         = None;
   nhdreclassification               = None;
   roadsreclassification             = None;
   ssurgoreclassification            = None;
   slopeweight                       = None;
   landcoverweight                   = None;
   nhdweight                         = None;
   roadsweight                       = None;
   ssurgoweight                      = None;
   selected_featurecount             = None;
   selected_areasqkm                 = None;
   mean_suitability_score            = None;
   available_solid_waste_capacity_m3 = None;
   available_liquid_waste_capacity_L = None;
   username                          = None;
   datecreated                       = None;
   lastupdate                        = None;
   notes                             = None;

   if scenario_id is not None:
      try:
         with arcpy.da.SearchCursor(
             aprx.defaultGeodatabase + os.sep + g_scenario_fc
            ,flds
         ) as cursor:
            for row in cursor:
               if row[0] == scenario_id:
                  analysis_complete                 = row[1];
                  aoi_id                            = row[2];
                  load_slope                        = row[3];
                  load_landcover                    = row[4];
                  load_nhd                          = row[5];
                  load_roads                        = row[6];
                  load_ssurgo                       = row[7];
                  slopegridsize                     = row[8];
                  landcovergridsize                 = row[9];
                  nhdgridsize                       = row[10];
                  roadsgridsize                     = row[11];
                  ssurgogridsize                    = row[12];
                  slopereclassification             = row[13];
                  landcoverreclassification         = row[14];
                  nhdreclassification               = row[15];
                  roadsreclassification             = row[16];
                  ssurgoreclassification            = row[17];
                  slopeweight                       = row[18];
                  landcoverweight                   = row[19];
                  nhdweight                         = row[20];
                  roadsweight                       = row[21];
                  ssurgoweight                      = row[22];
                  selected_featurecount             = row[23];
                  selected_areasqkm                 = row[24];
                  mean_suitability_score            = row[25];
                  available_solid_waste_capacity_m3 = row[26];
                  available_liquid_waste_capacity_L = row[27];
                  username                          = row[28];
                  datecreated                       = row[29];
                  lastupdate                        = row[30];
                  notes                             = row[31];
                  break;
                  
      except Exception as e:
         dzlog(str(sys.exc_info()),'ERROR');
         raise;
         
   if slopereclassification == 'None':
      slopereclassification = None;
   if landcoverreclassification == 'None':
      landcoverreclassification = None;
   if nhdreclassification == 'None':
      nhdreclassification = None;
   if roadsreclassification == 'None':
      roadsreclassification = None;
   if ssurgoreclassification == 'None':
      ssurgoreclassification = None;
  
   if slopeweight == 'None':
      slopeweight = None;
   if landcoverweight == 'None':
      landcoverweight = None;
   if nhdweight == 'None':
      nhdweight = None;
   if roadsweight == 'None':
      roadsweight = None;
   if ssurgoweight == 'None':
      ssurgoweight = None;
      
   return {
       "Analysis Complete"                  : str(analysis_complete or '')
      ,"Area of Interest ID"                : str(aoi_id or '')
      ,"Slope Grid Size (m2)"               : str(slopegridsize or '')
      ,"Land Cover Grid Size (m2)"          : str(landcovergridsize or '')
      ,"NHD Grid Size (m2)"                 : str(nhdgridsize or '') 
      ,"Roads Grid Size (m2)"               : str(roadsgridsize or '')
      ,"SSURGO Grid Size (m2)"              : str(ssurgogridsize or '')
      ,"Slope Reclassification"             : str(slopereclassification or '')
      ,"Land Cover Reclassification"        : str(landcoverreclassification or '')
      ,"NHD Reclassification"               : str(nhdreclassification or '')
      ,"Roads Reclassification"             : str(roadsreclassification or '')
      ,"SSURGO Reclassification"            : str(ssurgoreclassification or '')
      ,"Slope Weight Factor"                : str(slopeweight or '')
      ,"Land Cover Weight Factor"           : str(landcoverweight or '')
      ,"NHD Weight Factor"                  : str(nhdweight or '')
      ,"Roads Weight Factor"                : str(roadsweight or '')
      ,"SSURGO Weight Factor"               : str(ssurgoweight or '')
      ,"Selected Feature Count"             : str(selected_featurecount or '')
      ,"Selected Total Area (sqkm)"         : str(selected_areasqkm or '')
      ,"Mean Suitability Score"             : str(mean_suitability_score or '')
      ,"Available Solid Waste Capacity (m3)": str(available_solid_waste_capacity_m3 or '')
      ,"Available Liquid Waste Capacity (L)": str(available_liquid_waste_capacity_L or '')
      ,"Username"                           : str(username or '')
      ,"Date Created"                       : str(datecreated or '')
      ,"Date Last Updated"                  : str(lastupdate or '')
      ,"Notes"                              : str(notes or '')
   };

###############################################################################
def fetchScenarioCharacteristics(scenario_id,aprx=None):

   columns = [
       ['String','       Characteristic']
      ,['String','Value']
   ];
   
   cdict = fetchScenarioCharacteristics_dict(
       scenario_id = scenario_id
      ,aprx        = aprx
   );

   value = "\"Analysis Complete\" \""                   + cdict["Analysis Complete"]                   + "\";" \
         + "\"Area of Interest ID\" \""                 + cdict["Area of Interest ID"]                 + "\";" \
         + "\"Slope Grid Size (m2)\" \""                + cdict["Slope Grid Size (m2)"]                 + "\";" \
         + "\"Land Cover Grid Size (m2)\" \""           + cdict["Land Cover Grid Size (m2)"]            + "\";" \
         + "\"NHD Grid Size (m2)\" \""                  + cdict["NHD Grid Size (m2)"]                   + "\";" \
         + "\"Roads Grid Size (m2)\" \""                + cdict["Roads Grid Size (m2)"]                 + "\";" \
         + "\"SSURGO Grid Size (m2)\" \""               + cdict["SSURGO Grid Size (m2)"]                + "\";" \
         + "\"Slope Reclassification\" \""              + cdict["Slope Reclassification"]              + "\";" \
         + "\"Land Cover Reclassification\" \""         + cdict["Land Cover Reclassification"]         + "\";" \
         + "\"NHD Reclassification\" \""                + cdict["NHD Reclassification"]                + "\";" \
         + "\"Roads Reclassification\" \""              + cdict["Roads Reclassification"]              + "\";" \
         + "\"SSURGO Reclassification\" \""             + cdict["SSURGO Reclassification"]             + "\";" \
         + "\"Slope Weight Factor\" \""                 + cdict["Slope Weight Factor"]                 + "\";" \
         + "\"Land Cover Weight Factor\" \""            + cdict["Land Cover Weight Factor"]            + "\";" \
         + "\"NHD Weight Factor\" \""                   + cdict["NHD Weight Factor"]                   + "\";" \
         + "\"Roads Weight Factor\" \""                 + cdict["Roads Weight Factor"]                 + "\";" \
         + "\"SSURGO Weight Factor\" \""                + cdict["SSURGO Weight Factor"]                + "\";" \
         + "\"Selected Feature Count\" \""              + cdict["Selected Feature Count"]              + "\";" \
         + "\"Selected Total Area (sqkm)\" \""          + cdict["Selected Total Area (sqkm)"]          + "\";" \
         + "\"Mean Suitability Score\" \""              + cdict["Mean Suitability Score"]              + "\";" \
         + "\"Available Solid Waste Capacity (m3)\" \"" + cdict["Available Solid Waste Capacity (m3)"] + "\";" \
         + "\"Available Liquid Waste Capacity (L)\" \"" + cdict["Available Liquid Waste Capacity (L)"] + "\";" \
         + "\"Username\" \""                            + cdict["Username"]                            + "\";" \
         + "\"Date Created\" \""                        + cdict["Date Created"]                        + "\";" \
         + "\"Date Last Updated\" \""                   + cdict["Date Last Updated"]                   + "\";" \
         + "\"Notes\" \""                               + cdict["Notes"]                               + "\";";

   return (columns,value);
   
###############################################################################
def purgeFGDB(workspace):

   swap = arcpy.env.workspace;

   arcpy.env.workspace = workspace;

   for fc in arcpy.ListFeatureClasses('*'):
      arcpy.Delete_management(fc);

   for rs in arcpy.ListRasters('*'):
      arcpy.Delete_management(rs);

   for tb in arcpy.ListTables('*'):
      arcpy.Delete_management(tb);

   arcpy.env.workspace = swap;

###############################################################################
def sniffEditingState(workspace=None):

   if workspace is None:
      workspace = arcpy.env.workspace;

   boo_check = False;

   try:
      z = arcpy.da.Editor(workspace);
      z.startEditing(False,False);
      z.stopEditing(False);

   except:
      boo_check = True;

   return boo_check;
   
###############################################################################
def write_stash(stash_items,aprx=None):
   
   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);

   if not arcpy.Exists(aprx.defaultGeodatabase + os.sep + g_stash_tbl):
      
      arcpy.CreateTable_management(
          out_path          = aprx.defaultGeodatabase
         ,out_name          = g_stash_tbl
         ,config_keyword    = None
      );

      arcpy.management.AddFields(
          aprx.defaultGeodatabase + os.sep + g_stash_tbl
         ,[
             ['key'     ,'TEXT'  ,'Key'            ,255 ,None,'']
            ,['value'   ,'TEXT'  ,'Value'          ,255 ,None,'']
          ]
      );
      
   updates = [];
   
   with arcpy.da.SearchCursor(
       aprx.defaultGeodatabase + os.sep + g_stash_tbl
      ,['key']
   ) as cursor:
      for row in cursor:
         if row[0] in stash_items:
            updates.append(row[0]);
            
   with arcpy.da.UpdateCursor(
       aprx.defaultGeodatabase + os.sep + g_stash_tbl
      ,['key','value']
   ) as cursor:       
      for row in cursor:
         if row[0] in updates:
            cursor.updateRow((row[0],stash_items[row[0]]));
            
   with arcpy.da.InsertCursor(
       aprx.defaultGeodatabase + os.sep + g_stash_tbl
      ,['key','value']
   ) as cursor:
      for item in stash_items:
         if item not in updates:
            cursor.insertRow((item,stash_items[item]));
            
 ###############################################################################
def read_stash(aprx=None):

   if aprx is None:
      aprx = arcpy.mp.ArcGISProject(g_prj);

   if not arcpy.Exists(aprx.defaultGeodatabase + os.sep + g_stash_tbl):
      return {};
      
   rez = {};
   
   with arcpy.da.SearchCursor(
       aprx.defaultGeodatabase + os.sep + g_stash_tbl
      ,['key','value']
   ) as cursor:
      for row in cursor:
         rez[row[0]] = row[1];

   return rez;
   
###############################################################################
def buffer_extent(extent,percent):

   extBuffDistX = abs(extent.lowerLeft.X - extent.lowerRight.X) * percent / 2;
   extBuffDistY = abs(extent.lowerLeft.Y - extent.upperLeft.Y)  * percent / 2;
   
   newExtentPts = arcpy.Array();
   
   ptll = arcpy.Point();
   ptll.X = extent.lowerLeft.X - extBuffDistX;
   ptll.Y = extent.lowerLeft.Y - extBuffDistY;
   newExtentPts.add(ptll);
   
   ptlr = arcpy.Point();
   ptlr.X = extent.lowerRight.X + extBuffDistX;
   ptlr.Y = extent.lowerRight.Y - extBuffDistY;
   newExtentPts.add(ptlr);
   
   ptur = arcpy.Point();
   ptur.X = extent.upperRight.X + extBuffDistX;
   ptur.Y = extent.upperRight.Y + extBuffDistY;
   newExtentPts.add(ptur);
   
   ptul = arcpy.Point();
   ptul.X = extent.upperLeft.X - extBuffDistX;
   ptul.Y = extent.upperLeft.Y + extBuffDistY;
   newExtentPts.add(ptul);
   
   newExtentPts.add(ptll);

   newPolygon = arcpy.Polygon(newExtentPts);
   
   return newPolygon.extent;
