import arcpy;
import sys,os;
import datetime;
import util;
import openpyxl;
import logging;
import math;

import importlib;
cd = importlib.import_module('util');
importlib.reload(cd);
   
###############################################################################
class Toolbox(object):

   def __init__(self):

      self.label = "StorageStagingSiteTool";
      self.alias = "StorageStagingSiteTool";

      self.tools = [];
      self.tools.append(ConfirmSuitabilityCriteria);
      self.tools.append(SpecifyCriteriaWeight);
      self.tools.append(FinalizeStagingParcelSelection);
      self.tools.append(ExportSaveResults);

###############################################################################
class ConfirmSuitabilityCriteria(object):

   #...........................................................................
   def __init__(self):

      self.label              = "T1 Confirm Suitability Criteria";
      self.name               = "ConfirmSuitabilityCriteria";
      self.description        = "Confirm Suitability Criteria";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):
   
      #########################################################################\
      parm_enb       = True;
      scenarios      = [];
      def_scenario   = None;
      param1_columns = []
      param1_value   = None;
      mapnames       = [];
      def_mapname    = None;
      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      if not arcpy.Exists(aprx.defaultGeodatabase + os.sep + util.g_scenario_fc):
         err_val  = "Scenario Storage has not been initialized.";
         err_enb  = True;
         parm_enb = False;
      
      else:
         try:
            aprx = arcpy.mp.ArcGISProject(util.g_prj);
            scenarios,def_scenario = util.fetchScenarioIDs(aprx=aprx);
            mapnames,def_mapname   = util.fetchMapNames(aprx=aprx);
            
            (param1_columns,param1_value) = util.fetchScenarioCharacteristics(
                scenario_id = def_scenario
               ,aprx        = aprx
            );
            
            if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
               err_val = "Please save or delete all pending edits before proceeding.";
               err_enb = True;
            else:
               err_val = None;
               err_enb = False;
            
         except Exception as e:
            util.dzlog(str(sys.exc_info()),'error');
            raise;
            
      if len(scenarios) == 0:
         err_val  = "No scenarios found in system.";
         err_enb  = True;
         parm_enb = False;
          
      #########################################################################
      try:
         (
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
         ) = util.fetchReclassification(def_scenario,aprx);
         
      except Exception as e:
         util.dzlog(str(sys.exc_info()),'error');
         raise;
      
      #########################################################################
      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;

      #########################################################################
      param1 = arcpy.Parameter(
          displayName   = ''
         ,name          = "ScenarioCharacteristics"
         ,datatype      = "GPValueTable"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,category      = "Scenario Characteristics"
      );
      param1.columns = param1_columns;
      param1.value   = param1_value;

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "Scenario ID"
         ,name          = "ScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param2.filter.type = "ValueList";
      param2.filter.list = scenarios;
      param2.value       = def_scenario;

      ##---------------------------------------------------------------------##
      param3 = arcpy.Parameter(
          displayName   = "Map Name"
         ,name          = "MapName"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param3.filter.type = "ValueList";
      param3.filter.list = mapnames;
      param3.value       = def_mapname;

      ##---------------------------------------------------------------------##
      param4 = arcpy.Parameter(
          displayName   = "Slope Reclassification"
         ,name          = "SlopeReclassification"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      if slopeenabled:
         param4.value = slopereclassification;
      else:
         param4.value = "NA";
         
      ##---------------------------------------------------------------------##
      param5 = arcpy.Parameter(
          displayName   = "Land Cover Reclassification"
         ,name          = "LandCoverReclassification"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      if landcoverenabled:
         param5.value = landcoverreclassification;
      else:
         param5.value = "NA";
         
      ##---------------------------------------------------------------------##
      param6 = arcpy.Parameter(
          displayName   = "Surface Water Reclassification"
         ,name          = "SurfaceWaterReclassification"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      if nhdenabled:
         param6.value = nhdreclassification;
      else:
         param6.value = "NA";

      ##---------------------------------------------------------------------##
      param7 = arcpy.Parameter(
          displayName   = "Road Reclassification"
         ,name          = "RoadReclassification"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      if roadsenabled:
         param7.value = roadsreclassification;
      else:
         param7.value = "NA";

      ##---------------------------------------------------------------------##
      param8 = arcpy.Parameter(
          displayName   = "Soil Group Reclassification"
         ,name          = "SoilGroupReclassification"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      if ssurgoenabled:
         param8.value = ssurgoreclassification;
      else:
         param8.value = "NA";

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
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      if parameters[2].altered and not parameters[2].hasBeenValidated:
         aprx = arcpy.mp.ArcGISProject(util.g_prj);
         
         (columns,value) = util.fetchScenarioCharacteristics(
             scenario_id = parameters[2].value
            ,aprx        = aprx
         );
         
         parameters[1].value   = value;
         
         (
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
         ) = util.fetchReclassification(parameters[2].value,aprx);
         
         parameters[4].value = slopereclassification;
         parameters[5].value = landcoverreclassification;
         parameters[6].value = nhdreclassification;
         parameters[7].value = roadsreclassification;
         parameters[8].value = ssurgoreclassification;
      
      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;
      
   #...........................................................................
   def execute(self,parameters,messages):

      scenario_id = parameters[2].valueAsText;
      if scenario_id == "" or scenario_id == " ":
         scenario_id = None;
      map_name = parameters[3].valueAsText;
      if map_name == "" or map_name == " ":
         map_name = None;
      slope_reclassification = parameters[4].valueAsText;
      if slope_reclassification == "" or slope_reclassification == " " or slope_reclassification == "NA":
         slope_reclassification = None;
      landcover_reclassification = parameters[5].valueAsText;
      if landcover_reclassification == "" or landcover_reclassification == " " or landcover_reclassification == "NA":
         landcover_reclassification = None;
      nhd_reclassification = parameters[6].valueAsText;
      if nhd_reclassification == "" or nhd_reclassification == " " or nhd_reclassification == "NA":
         nhd_reclassification = None;
      roads_reclassification = parameters[7].valueAsText;
      if roads_reclassification == "" or roads_reclassification == " " or roads_reclassification == "NA":
         roads_reclassification = None;
      ssurgo_reclassification = parameters[8].valueAsText;
      if ssurgo_reclassification == "" or ssurgo_reclassification == " " or ssurgo_reclassification == "NA":
         ssurgo_reclassification = None;
         
      arcpy.env.overwriteOutput = True;
      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      rez = arcpy.CheckOutExtension("Spatial");
      if rez != "CheckedOut":
         rez = arcpy.CheckOutExtension("ImageAnalyst");
         if rez != "CheckedOut":
            arcpy.AddMessage("Unable to check out spatial or image analyst extension");

      rast = os.path.join(aprx.defaultGeodatabase,scenario_id + "_EXTRACT_SLOPE");
      if arcpy.Exists(rast):
         in_slope = rast;
      else:
         in_slope = None;
      
      rast = os.path.join(aprx.defaultGeodatabase,scenario_id + "_EXTRACT_LANDCOVER");
      if arcpy.Exists(rast):
         in_landcover = rast;
      else:
         in_landcover = None;
      
      rast = os.path.join(aprx.defaultGeodatabase,scenario_id + "_EXTRACT_NHD");
      if arcpy.Exists(rast):
         in_nhd = rast;
      else:
         in_nhd = None;
      
      rast = os.path.join(aprx.defaultGeodatabase,scenario_id + "_EXTRACT_ROADS");
      if arcpy.Exists(rast):
         in_roads = rast;
      else:
         in_roads = None;
      
      rast = os.path.join(aprx.defaultGeodatabase,scenario_id + "_EXTRACT_SSURGO");
      if arcpy.Exists(rast):
         in_ssurgo = rast;
      else:
         in_ssurgo = None;

      inTrueRaster    = 0;
      inFalseConstant = 1;

      #########################################################################
      # arcpy.sa.Con requires one of:
      #  Spatial Analyst
      #  Image Analyst
      #########################################################################
      if in_slope is not None:
         arcpy.AddMessage(".  Processing Slope...");
         out_slope = arcpy.sa.Con(
             in_slope
            ,inTrueRaster
            ,inFalseConstant
            ,slope_reclassification
         );
         out_slope.save(os.path.join(aprx.defaultGeodatabase,scenario_id + "_RECLASS_SLOPE"));
      
      if in_landcover is not None:      
         arcpy.AddMessage(".  Processing Land Cover...");
         out_landcover = arcpy.sa.Con(
             in_landcover
            ,inTrueRaster
            ,inFalseConstant
            ,landcover_reclassification
         );
         out_landcover.save(os.path.join(aprx.defaultGeodatabase,scenario_id + "_RECLASS_LANDCOVER"));
      
      if in_nhd is not None:
         arcpy.AddMessage(".  Processing NHD...");
         out_nhd = arcpy.sa.Con(
             in_nhd
            ,inTrueRaster
            ,inFalseConstant
            ,nhd_reclassification
         );
         out_nhd.save(os.path.join(aprx.defaultGeodatabase,scenario_id + "_RECLASS_NHD"));
      
      if in_roads is not None:
         arcpy.AddMessage(".  Processing Roads...");
         out_roads = arcpy.sa.Con(
             in_roads
            ,inTrueRaster
            ,inFalseConstant
            ,roads_reclassification
         );
         out_roads.save(os.path.join(aprx.defaultGeodatabase,scenario_id + "_RECLASS_ROADS"));

      if in_ssurgo is not None:
         arcpy.AddMessage(".  Processing SSURGO...");
         out_ssurgo = arcpy.sa.Con(
             in_ssurgo
            ,inTrueRaster
            ,inFalseConstant
            ,ssurgo_reclassification
         );
         out_ssurgo.save(os.path.join(aprx.defaultGeodatabase,scenario_id + "_RECLASS_SSURGO"));

      if slope_reclassification is None:
         slope_reclassification = 'None';
      if landcover_reclassification is None:
         landcover_reclassification = 'None';
      if nhd_reclassification is None:
         nhd_reclassification = 'None';
      if roads_reclassification is None:
         roads_reclassification = 'None';   
      if ssurgo_reclassification is None:
         ssurgo_reclassification = 'None';

      with arcpy.da.UpdateCursor(
          aprx.defaultGeodatabase + os.sep + util.g_scenario_fc
         ,[
             'scenario_id'
            ,'analysis_complete'
            ,'slopereclassification'
            ,'landcoverreclassification'
            ,'nhdreclassification'
            ,'roadsreclassification'
            ,'ssurgoreclassification'
            ,'lastupdate'
         ]
      ) as cursor:
         for row in cursor:
            if row[0] == scenario_id:
               row[1]  = 'N'
               row[2]  = slope_reclassification;
               row[3]  = landcover_reclassification;
               row[4]  = nhd_reclassification;
               row[5]  = roads_reclassification;
               row[6]  = ssurgo_reclassification;
               row[7]  = datetime.datetime.now();
               cursor.updateRow(row);
               break;

      util.write_stash({"scenario_id":scenario_id},aprx=aprx);      
      
###############################################################################
class SpecifyCriteriaWeight(object):

   #...........................................................................
   def __init__(self):

      self.label              = "T2 Specify Criteria Weight";
      self.name               = "SpecifyCriteriaWeight";
      self.description        = "Specify Criteria Weight";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      #########################################################################\
      parm_enb       = True;
      scenarios      = [];
      def_scenario   = None;
      param1_columns = []
      param1_value   = None;
      mapnames       = [];
      def_mapname    = None;
      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      if not arcpy.Exists(aprx.defaultGeodatabase + os.sep + util.g_scenario_fc):
         err_val  = "Scenario Storage has not been initialized.";
         err_enb  = True;
         parm_enb = False;
      
      else:
         try:
            scenarios,def_scenario = util.fetchScenarioIDs(aprx=aprx);
            mapnames,def_mapname   = util.fetchMapNames(aprx=aprx);
            
            (param1_columns,param1_value) = util.fetchScenarioCharacteristics(
                scenario_id = def_scenario
               ,aprx        = aprx
            );
            
            if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
               err_val = "Please save or delete all pending edits before proceeding.";
               err_enb = True;
            else:
               err_val = None;
               err_enb = False;
            
         except Exception as e:
            util.dzlog(str(sys.exc_info()),'error');
            raise;
            
      if len(scenarios) == 0:
         err_val  = "No scenarios found in system.";
         err_enb  = True;
         parm_enb = False;
         
      #########################################################################
      try:
         (
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
         ) = util.fetchWeights(def_scenario,aprx);
         
      except Exception as e:
         util.dzlog(str(sys.exc_info()),'error');
         raise;
      
      #########################################################################
      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      #########################################################################
      param1 = arcpy.Parameter(
          displayName   = ''
         ,name          = "ScenarioCharacteristics"
         ,datatype      = "GPValueTable"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,category      = "Scenario Characteristics"
      );
      param1.columns = param1_columns;
      param1.value   = param1_value;

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "Scenario ID"
         ,name          = "ScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param2.filter.type = "ValueList";
      param2.filter.list = scenarios;
      param2.value       = def_scenario;

      ##---------------------------------------------------------------------##
      param3 = arcpy.Parameter(
          displayName   = "Map Name"
         ,name          = "MapName"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param3.filter.type = "ValueList";
      param3.filter.list = mapnames;
      param3.value       = def_mapname;

      ##---------------------------------------------------------------------##
      param4 = arcpy.Parameter(
          displayName   = "Slope Weight"
         ,name          = "SlopeWeight"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      if slopeenabled:
         param4.value = slopeweight;
      else:
         param4.value = "NA";
         
      ##---------------------------------------------------------------------##
      param5 = arcpy.Parameter(
          displayName   = "Land Cover Weight"
         ,name          = "LandCoverWeight"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      if landcoverenabled:
         param5.value = landcoverweight;
      else:
         param5.value = "NA";

      ##---------------------------------------------------------------------##
      param6 = arcpy.Parameter(
          displayName   = "Surface Water Weight"
         ,name          = "SurfaceWaterWeight"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      if nhdenabled:
         param6.value = nhdweight;
      else:
         param6.value = "NA";

      ##---------------------------------------------------------------------##
      param7 = arcpy.Parameter(
          displayName   = "Roads Weight"
         ,name          = "RoadsWeight"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      if roadsenabled:
         param7.value = roadsweight;
      else:
         param7.value = "NA";

      ##---------------------------------------------------------------------##
      param8 = arcpy.Parameter(
          displayName   = "Soil Type Weight"
         ,name          = "SoilTypeWeight"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      if ssurgoenabled:
         param8.value = ssurgoweight;
      else:
         param8.value = "NA";
      
      ##---------------------------------------------------------------------##
      param9 = arcpy.Parameter(
          displayName   = "Simplify Polygons"
         ,name          = "Simplify Polygons"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param9.value = True;

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
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      if parameters[2].altered and not parameters[2].hasBeenValidated:
         aprx = arcpy.mp.ArcGISProject(util.g_prj);
         
         (columns,value) = util.fetchScenarioCharacteristics(
             scenario_id = parameters[2].value
            ,aprx        = aprx
         );
         
         parameters[1].value   = value;
         
         (
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
         ) = util.fetchWeights(parameters[2].value,aprx);
         
         parameters[4].value = slopeweight;
         parameters[5].value = landcoverweight;
         parameters[6].value = nhdweight;
         parameters[7].value = roadsweight;
         parameters[8].value = ssurgoweight;
      
      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      scenario_id = parameters[2].valueAsText;
      if scenario_id == "" or scenario_id == " ":
         scenario_id = None;
      
      map_name = parameters[3].valueAsText;
      if map_name == "" or map_name == " ":
         map_name = None;
      
      slopeweight = parameters[4].valueAsText;
      if slopeweight == "" or slopeweight == " " or slopeweight == "NA":
         slopeweight = None;
      
      landcoverweight = parameters[5].valueAsText;
      if landcoverweight == "" or landcoverweight == " " or landcoverweight == "NA":
         landcoverweight = None;
      
      nhdweight = parameters[6].valueAsText;
      if nhdweight == "" or nhdweight == " " or nhdweight == "NA":
         nhdweight = None;
      
      roadsweight = parameters[7].valueAsText;
      if roadsweight == "" or roadsweight == " " or roadsweight == "NA":
         roadsweight = None;
      
      ssurgoweight = parameters[8].valueAsText;
      if ssurgoweight == "" or ssurgoweight == " " or ssurgoweight == "NA":
         ssurgoweight = None;

      str_simplify = parameters[9].valueAsText;
      if str_simplify in ['true','TRUE','1','Yes','Y']:
         str_simplify = 'SIMPLIFY';
      else:
         str_simplify = 'NO_SIMPLIFY'; 
         
      arcpy.env.overwriteOutput = True;
      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      map = aprx.listMaps(map_name)[0];
      
      rez = arcpy.CheckOutExtension("Spatial");
      if rez != "CheckedOut":
         rez = arcpy.CheckOutExtension("ImageAnalyst");
         if rez != "CheckedOut":
            rez = arcpy.CheckOutExtension("3D");
            if rez != "CheckedOut":
               arcpy.AddMessage("Unable to check out 3D analyst, spatial or image analyst extension");
      
      ##---------------------------------------------------------------------##
      # Decide whether to utilize the memory workspace or the scratch workspace
      d = arcpy.GetInstallInfo();
      
      if d['Version'][:3] == '2.3':
         wrkGDB = arcpy.env.scratchGDB;
         
      else:
         wrkGDB = 'memory';      
      
      ary_weights = [];
      
      if slopeweight is not None:
         arcpy.AddMessage(".  Weighting Slope...");
         
         in_slope = os.path.join(aprx.defaultGeodatabase,scenario_id + "_RECLASS_SLOPE");
         util.addFieldCalc(
             in_table          = in_slope
            ,field_name        = "weight"
            ,field_type        = "DOUBLE"
            ,field_alias       = "Weight"
            ,field_is_nullable = True
            ,calc_value        = slopeweight
         );
         util.addFieldCalc(
             in_table          = in_slope
            ,field_name        = "finalweight"
            ,field_type        = "DOUBLE"
            ,field_alias       = "FinalWeight"
            ,field_is_nullable = True
            ,calc_value        = "!Value! * !Weight!"
         );
         ary_weights.append([in_slope,"finalweight",1]);

      if landcoverweight is not None:
         arcpy.AddMessage(".  Weighting Land Cover...");
         
         in_landcover = os.path.join(aprx.defaultGeodatabase,scenario_id + "_RECLASS_LANDCOVER");
         util.addFieldCalc(
             in_table          = in_landcover
            ,field_name        = "weight"
            ,field_type        = "DOUBLE"
            ,field_alias       = "Weight"
            ,field_is_nullable = True
            ,calc_value        = landcoverweight
         );
         util.addFieldCalc(
             in_table          = in_landcover
            ,field_name        = "finalweight"
            ,field_type        = "DOUBLE"
            ,field_alias       = "FinalWeight"
            ,field_is_nullable = True
            ,calc_value        = "!Value! * !Weight!"
         );
         ary_weights.append([in_landcover,"finalweight",1]);

      if nhdweight is not None:
         arcpy.AddMessage(".  Weighting NHD...");
         
         in_nhd = os.path.join(aprx.defaultGeodatabase,scenario_id + "_RECLASS_NHD");
         util.addFieldCalc(
             in_table          = in_nhd
            ,field_name        = "weight"
            ,field_type        = "DOUBLE"
            ,field_alias       = "Weight"
            ,field_is_nullable = True
            ,calc_value        = nhdweight
         );
         util.addFieldCalc(
             in_table          = in_nhd
            ,field_name        = "finalweight"
            ,field_type        = "DOUBLE"
            ,field_alias       = "FinalWeight"
            ,field_is_nullable = True
            ,calc_value        = "!Value! * !Weight!"
         );
         ary_weights.append([in_nhd,"finalweight",1]);

      if roadsweight is not None:
         arcpy.AddMessage(".  Weighting Roads...");
         
         in_roads = os.path.join(aprx.defaultGeodatabase,scenario_id + "_RECLASS_ROADS");
         util.addFieldCalc(
             in_table          = in_roads
            ,field_name        = "weight"
            ,field_type        = "DOUBLE"
            ,field_alias       = "Weight"
            ,field_is_nullable = True
            ,calc_value        = roadsweight
         );
         util.addFieldCalc(
             in_table          = in_roads
            ,field_name        = "finalweight"
            ,field_type        = "DOUBLE"
            ,field_alias       = "FinalWeight"
            ,field_is_nullable = True
            ,calc_value        = "!Value! * !Weight!"
         );
         ary_weights.append([in_roads,"finalweight",1]);

      if ssurgoweight is not None:
         arcpy.AddMessage(".  Weighting SSURGO...");
         
         in_ssurgo = os.path.join(aprx.defaultGeodatabase,scenario_id + "_RECLASS_SSURGO");
         util.addFieldCalc(
             in_table          = in_ssurgo
            ,field_name        = "weight"
            ,field_type        = "DOUBLE"
            ,field_alias       = "Weight"
            ,field_is_nullable = True
            ,calc_value        = ssurgoweight
         );
         util.addFieldCalc(
             in_table          = in_ssurgo
            ,field_name        = "finalweight"
            ,field_type        = "DOUBLE"
            ,field_alias       = "FinalWeight"
            ,field_is_nullable = True
            ,calc_value        = "!Value! * !Weight!"
         );
         ary_weights.append([in_ssurgo,"finalweight",1]);

      arcpy.AddMessage(".  Generating weighted sums...");
      
      #########################################################################
      # arcpy.sa.Int requires one of:
      #  3D analyst
      #  Spatial analyst
      #  Image analyst
      #########################################################################
      outWeightedSum = arcpy.sa.Int(
         arcpy.sa.WeightedSum(
            arcpy.sa.WSTable(ary_weights)
         )
      );

      outWeightedSum.save(wrkGDB + os.sep + "scratch_" + scenario_id);

      arcpy.AddMessage(".  Converting to polygons...");
      weightedsum = os.path.join(aprx.defaultGeodatabase,scenario_id + "_WEIGHTEDSUM");
      
      #########################################################################
      # arcpy.RasterToPolygon_conversion available BASIC no extensions needed
      #########################################################################
      rez = arcpy.RasterToPolygon_conversion(
          in_raster            = wrkGDB + os.sep + "scratch_" + scenario_id
         ,out_polygon_features = weightedsum
         ,simplify             = str_simplify
         ,raster_field         = "VALUE"
      );
      
      if rez.status == 4:
         arcpy.AddMessage(".  Polygon conversion completed successfully.");
      else:
         raise Error("raster to polygon process failed with status " + str(rez.status));

      arcpy.AddMessage(".  Postprocessing...");
      arcpy.Delete_management(
         wrkGDB + os.sep + "scratch_" + scenario_id
      );

      util.addField(
          in_table          = weightedsum
         ,field_name        = "name"
         ,field_type        = "TEXT"
         ,field_alias       = "Name"
         ,field_is_nullable = True
      );

      util.addField(
          in_table          = weightedsum
         ,field_name        = "contamination_type"
         ,field_type        = "TEXT"
         ,field_alias       = "Contamination Type"
         ,field_is_nullable = True
      );

      desc = arcpy.Describe(weightedsum);
      flds = desc.fields;
      for fld in flds:
         if fld.name.lower() == "gridcode":
            arcpy.AlterField_management(
                in_table        = weightedsum
               ,field           = 'gridcode'
               ,new_field_name  = 'suitability_score'
               ,new_field_alias = 'Suitability Score'
            );

      util.addFieldCalc(
          in_table          = weightedsum
         ,field_name        = "areasqkm"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Geodetic Area (SqKm)"
         ,field_is_nullable = True
         ,calc_value        = "!Shape.geodesicArea@SQUAREKILOMETERS!"
      );

      util.addFieldCalc(
          in_table          = weightedsum
         ,field_name        = "available_solid_waste_capacity_m3"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Available Solid Waste Capacity (m3)"
         ,field_is_nullable = True
         ,calc_value        = "!areasqkm! * 1000000 * 0.4 / 0.3284"
      );

      util.addFieldCalc(
          in_table          = weightedsum
         ,field_name        = "available_liquid_waste_capacity_L"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Available Liquid Waste Capacity (L)"
         ,field_is_nullable = True
         ,calc_value        = "!areasqkm! * 1000000 * 0.4 / 0.0020975"
      );
      
      util.addFieldCalc(
          in_table          = weightedsum
         ,field_name        = "available_liquid_waste_capacity_m3"
         ,field_type        = "DOUBLE"
         ,field_alias       = "Available Liquid Waste Capacity (m3)"
         ,field_is_nullable = True
         ,calc_value        = "(!areasqkm! * 1000000 * 0.4 / 0.0020975) * 0.001"
      );
      
      util.addField(
          in_table          = weightedsum
         ,field_name        = "notes"
         ,field_type        = "TEXT"
         ,field_alias       = "Notes"
         ,field_is_nullable = True
      );

      if len(map.listLayers(scenario_id + "_WeightedSum")) == 0:
         lyrx = util.tempLyrx(
             in_layerfile = os.path.join(aprx.homeFolder,"WeightedSum.lyrx")
            ,dataset      = scenario_id + "_WEIGHTEDSUM"
            ,name         = scenario_id + "_WeightedSum"
            ,aprx         = aprx
         );
         lyr = arcpy.mp.LayerFile(lyrx);
         map.addLayer(lyr);
         
      if slopeweight is None:
         slopeweight = 'None';
      if landcoverweight is None:
         landcoverweight = 'None';
      if nhdweight is None:
         nhdweight = 'None';
      if roadsweight is None:
         roadsweight = 'None';   
      if ssurgoweight is None:
         ssurgoweight = 'None';

      with arcpy.da.UpdateCursor(
          in_table    = aprx.defaultGeodatabase + os.sep + util.g_scenario_fc
         ,field_names = [
             'scenario_id'
            ,'analysis_complete'
            ,'slopeweight'
            ,'landcoverweight'
            ,'nhdweight'
            ,'roadsweight'
            ,'ssurgoweight'
            ,'lastupdate'
         ]
      ) as cursor:
         for row in cursor:
            if row[0] == scenario_id:
               row[1]  = 'N';
               row[2]  = slopeweight;
               row[3]  = landcoverweight;
               row[4]  = nhdweight;
               row[5]  = roadsweight;
               row[6]  = ssurgoweight;
               row[7]  = datetime.datetime.now();
               cursor.updateRow(row);
               break;

      util.write_stash({"scenario_id":scenario_id},aprx=aprx);

###############################################################################
class FinalizeStagingParcelSelection(object):

   #...........................................................................
   def __init__(self):

      self.label              = "T3 Finalize Staging Parcel Selection";
      self.name               = "FinalizeStagingParcelSelection";
      self.description        = "Finalize Staging Parcel Selection";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):

      #########################################################################
      parm_enb       = True;
      scenarios      = [];
      def_scenario   = None;
      param1_columns = []
      param1_value   = None;
      mapnames       = [];
      def_mapname    = None;
      weightedsumlayer = None;
      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      if not arcpy.Exists(aprx.defaultGeodatabase + os.sep + util.g_scenario_fc):
         err_val  = "Scenario Storage has not been initialized.";
         err_enb  = True;
         parm_enb = False;
      
      else:
         try:
            aprx = arcpy.mp.ArcGISProject(util.g_prj);
            scenarios,def_scenario = util.fetchScenarioIDs(aprx=aprx);
            mapnames,def_mapname   = util.fetchMapNames(aprx=aprx);
            weightedsumlayer       = util.fetchWeightedSumLayer(aprx=aprx);
            
            (param1_columns,param1_value) = util.fetchScenarioCharacteristics(
                scenario_id = def_scenario
               ,aprx        = aprx
            );
            
            if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
               err_val = "Please save or delete all pending edits before proceeding.";
               err_enb = True;
            else:
               err_val = None;
               err_enb = False;
            
         except Exception as e:
            util.dzlog(str(sys.exc_info()),'error');
            raise;
            
      if len(scenarios) == 0:
         err_val  = "No scenarios found in system.";
         err_enb  = True;
         parm_enb = False;
      
      #########################################################################
      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;
      
      #########################################################################
      param1 = arcpy.Parameter(
          displayName   = ''
         ,name          = "ScenarioCharacteristics"
         ,datatype      = "GPValueTable"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,category      = "Scenario Characteristics"
      );
      param1.columns = param1_columns;
      param1.value   = param1_value;

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "Scenario ID"
         ,name          = "ScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param2.filter.type = "ValueList";
      param2.filter.list = scenarios;
      param2.value       = def_scenario;

      ##---------------------------------------------------------------------##
      param3 = arcpy.Parameter(
          displayName   = "Map Name"
         ,name          = "MapName"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param3.filter.type = "ValueList";
      param3.filter.list = mapnames;
      param3.value       = def_mapname;

      ##---------------------------------------------------------------------##
      param4 = arcpy.Parameter(
          displayName   = "Weighted Sum Layer"
         ,name          = "Weighted Sum Layer"
         ,datatype      = "GPLayer"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param4.value = weightedsumlayer;
      
      ##---------------------------------------------------------------------##
      param5 = arcpy.Parameter(
          displayName   = "Aggregate Results Polygon"
         ,name          = "Aggregate Results Polygon"
         ,datatype      = "GPBoolean"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param5.value = True;

      params = [
          param0
         ,param1
         ,param2
         ,param3
         ,param4
         ,param5
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      if parameters[2].altered and not parameters[2].hasBeenValidated:
         aprx = arcpy.mp.ArcGISProject(util.g_prj);
         
         (columns,value) = util.fetchScenarioCharacteristics(
             scenario_id = parameters[2].value
            ,aprx        = aprx
         );
         
         parameters[1].value   = value;
      
      return;

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):

      scenario_id = parameters[2].valueAsText;
      if scenario_id == "" or scenario_id == " ":
         scenario_id = None;
      
      map_name = parameters[3].valueAsText;
      if map_name == "" or map_name == " ":
         map_name = None;
      
      weightedsum = parameters[4].value;
      if weightedsum == "" or weightedsum == " ":
         weightedsum = None;
      
      str_dissolve = parameters[5].valueAsText;
      if str_dissolve in ['true','TRUE','1','Yes','Y']:
         boo_dissolve = True;
      else:
         boo_dissolve = False; 

      arcpy.env.overwriteOutput = True;
      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      map = aprx.listMaps(map_name)[0];
      
      result = arcpy.GetCount_management(weightedsum);
      int_selected_count = int(result.getOutput(0));
      
      if int_selected_count == 0:
         raise Exception("Error, no parcels selected.");
      arcpy.AddMessage(".  Found " + str(int_selected_count) + " selected parcels...");     
      
      #########################################################################
      selected = os.path.join(aprx.defaultGeodatabase,scenario_id + "_SELECTED");
      
      if arcpy.Exists(selected):
         arcpy.Delete_management(selected);
         
      arcpy.CreateFeatureclass_management(
          out_path          = aprx.defaultGeodatabase
         ,out_name          = scenario_id + "_SELECTED"
         ,geometry_type     = "POLYGON"
         ,has_m             = "DISABLED"
         ,has_z             = "DISABLED"
         ,spatial_reference = arcpy.SpatialReference(util.g_srid)
         ,config_keyword    = None
      );

      arcpy.management.AddFields(
          selected
         ,[
             ['id'                                ,'LONG'  ,'ID'                                  ,None,None,'']
            ,['name'                              ,'TEXT'  ,'Name'                                ,255 ,None,'']
            ,['contamination_type'                ,'TEXT'  ,'Contamination Type'                  ,255 ,None,'']
            ,['suitability_score'                 ,'LONG'  ,'Suitability Score'                   ,None,None,'']
            ,['areasqkm'                          ,'DOUBLE','Geodetic Area (SqKm)'                ,None,None,'']
            ,['available_solid_waste_capacity_m3' ,'DOUBLE','Available Solid Waste Capacity (m3)' ,None,None,'']
            ,['available_liquid_waste_capacity_L' ,'DOUBLE','Available Liquid Waste Capacity (L)' ,None,None,'']
            ,['available_liquid_waste_capacity_m3','DOUBLE','Available Liquid Waste Capacity (m3)',None,None,'']
          ]
      );
      
      arcpy.CopyFeatures_management(
          in_features       = weightedsum
         ,out_feature_class = selected
      );
      
      #########################################################################
      sitingstaging = os.path.join(aprx.defaultGeodatabase,scenario_id + "_STAGINGSITESELECTION");
      
      if arcpy.Exists(sitingstaging):
         arcpy.Delete_management(sitingstaging);
         
      arcpy.CreateFeatureclass_management(
          out_path          = aprx.defaultGeodatabase
         ,out_name          = scenario_id + "_STAGINGSITESELECTION"
         ,geometry_type     = "POLYGON"
         ,has_m             = "DISABLED"
         ,has_z             = "DISABLED"
         ,spatial_reference = arcpy.SpatialReference(util.g_srid)
         ,config_keyword    = None
      );

      arcpy.management.AddFields(
          sitingstaging
         ,[
             ['name'                                  ,'TEXT'  ,'Name'                                ,255 ,None,'']
            ,['contamination_type'                    ,'TEXT'  ,'Contamination Type'                  ,255 ,None,'']
            ,['MEAN_suitability_score'                ,'DOUBLE','Mean Suitability Score'              ,None,None,'']
            ,['SUM_areasqkm'                          ,'DOUBLE','Geodetic Area (SqKm)'                ,None,None,'']
            ,['SUM_available_solid_waste_capacity_m3' ,'DOUBLE','Available Solid Waste Capacity (m3)' ,None,None,'']
            ,['SUM_available_liquid_waste_capacity_L' ,'DOUBLE','Available Liquid Waste Capacity (L)' ,None,None,'']
            ,['SUM_available_liquid_waste_capacity_m3','DOUBLE','Available Liquid Waste Capacity (m3)',None,None,'']
            ,['CENTROID_X'                            ,'DOUBLE','Centroid Longitude'                  ,None,None,'']
            ,['CENTROID_Y'                            ,'DOUBLE','Centroid Latitude'                   ,None,None,'']
            ,['FIRST_notes'                           ,'TEXT'  ,'Notes'                               ,255 ,None,'']
          ]
      );
      
      #########################################################################
      def xstr(s):
         return s if s else '';
         
      flds = [
          'name'
         ,'contamination_type'
      ];
      
      #########################################################################
      if not boo_dissolve:
         arcpy.AddMessage(".  Totaling...");
      
         keys = {};
         with arcpy.da.SearchCursor(
             selected
            ,flds
         ) as cursor:
            for row in cursor:
               r = 'K' + xstr(row[0]) + xstr(row[1]);
               if r not in keys:
                  keys[r] = {};
               
         arcpy.AddMessage("Found " + str(len(keys)) + " grouping keys to aggregate upon.");
      
      #########################################################################
         flds = [
             'name'
            ,'contamination_type'
            ,'suitability_score'
            ,'areasqkm'
            ,'available_solid_waste_capacity_m3'
            ,'available_liquid_waste_capacity_L'
            ,'available_liquid_waste_capacity_m3'
            ,'notes'
         ];
         
         with arcpy.da.SearchCursor(
             selected
            ,flds
         ) as cursor:
         
            for row in cursor:
               r = 'K' + xstr(row[0]) + xstr(row[1]);
               
               if 'areasqkm' not in keys[r]:
               
                  keys[r] = {
                      'name'                              : row[0]
                     ,'contamination_type'                : row[1]
                     ,'suitability_score'                 : row[2]
                     ,'areasqkm'                          : row[3]
                     ,'available_solid_waste_capacity_m3' : row[4]
                     ,'available_liquid_waste_capacity_L' : row[5]
                     ,'available_liquid_waste_capacity_m3': row[6]
                     ,'notes'                             : row[7]
                     ,'count'                             : 1
                  };
                  
               else:
               
                  keys[r]['suitability_score']                  += row[2];
                  keys[r]['areasqkm']                           += row[3];
                  keys[r]['available_solid_waste_capacity_m3']  += row[4];
                  keys[r]['available_liquid_waste_capacity_L']  += row[5];
                  keys[r]['available_liquid_waste_capacity_m3'] += row[6];
                  keys[r]['count']                              += 1;
                     
         ######################################################################
         outflds = [
             'name'
            ,'contamination_type'
            ,'MEAN_Suitability_Score'
            ,'SUM_areasqkm'
            ,'SUM_available_solid_waste_capacity_m3'
            ,'SUM_available_liquid_waste_capacity_L'
            ,'SUM_available_liquid_waste_capacity_m3'
            ,'FIRST_notes'
         ];
         with arcpy.da.InsertCursor(
             sitingstaging
            ,outflds
         ) as insert_rows:
         
            for item in keys:
            
               insert_rows.insertRow((
                   keys[item]['name']
                  ,keys[item]['contamination_type']
                  ,keys[item]['suitability_score'] / keys[item]['count']
                  ,keys[item]['areasqkm']
                  ,keys[item]['available_solid_waste_capacity_m3']
                  ,keys[item]['available_liquid_waste_capacity_L']
                  ,keys[item]['available_liquid_waste_capacity_m3']
                  ,keys[item]['notes']
               ));

      else:
         arcpy.AddMessage(".  Aggregating...");
         
         #########################################################################
         # arcpy.PairwiseDissolve_analysis requires no special licensing
         #########################################################################
         arcpy.PairwiseDissolve_analysis(
             in_features       = selected
            ,out_feature_class = sitingstaging
            ,dissolve_field    = ["name","contamination_type"]
            ,statistics_fields = [
                ["suitability_score"                 ,"MEAN"]
               ,["areasqkm"                          ,"SUM"]
               ,["available_solid_waste_capacity_m3" ,"SUM"]
               ,["available_liquid_waste_capacity_L" ,"SUM"]
               ,["available_liquid_waste_capacity_m3","SUM"]
               ,["notes"                             ,"FIRST"]
             ]
            ,multi_part        = "MULTI_PART"
         );

         #########################################################################
         # arcpy.AddGeometryAttributes_management requires no special licensing
         #########################################################################
         arcpy.AddGeometryAttributes_management(
             Input_Features      = sitingstaging
            ,Geometry_Properties = "CENTROID"
            ,Coordinate_System   = arcpy.SpatialReference(4326)
         );

      #########################################################################
      if len(map.listLayers(scenario_id + "_StagingSiteSelection")) == 0:
         lyrx = util.tempLyrx(
             in_layerfile = os.path.join(aprx.homeFolder,"StagingSiteSelection.lyrx")
            ,dataset      = scenario_id + "_STAGINGSITESELECTION"
            ,name         = scenario_id + "_StagingSiteSelection"
            ,aprx         = aprx
         );
         lyr = arcpy.mp.LayerFile(lyrx);
         map.addLayer(lyr);

      num_areasqkm     = 0;
      num_solid_waste  = 0;
      num_liquid_waste = 0;
      with arcpy.da.SearchCursor(
          sitingstaging
         ,[
             'MEAN_suitability_score'
            ,'SUM_areasqkm'
            ,'SUM_available_solid_waste_capacity_m3'
            ,'SUM_available_liquid_waste_capacity_L'
            ,'SUM_available_liquid_waste_capacity_m3'
          ]
      ) as cursor:
         for row in cursor:
            num_mean_score    = row[0];
            num_areasqkm     += row[1];
            num_solid_waste  += row[2];
            num_liquid_waste += row[3];

      with arcpy.da.UpdateCursor(
          aprx.defaultGeodatabase + os.sep + util.g_scenario_fc
         ,[
             'scenario_id'
            ,'analysis_complete'
            ,'selected_featurecount'
            ,'selected_areasqkm'
            ,'mean_suitability_score'
            ,'available_solid_waste_capacity_m3'
            ,'available_liquid_waste_capacity_L'
            ,'lastupdate'
         ]
      ) as cursor:
         for row in cursor:
            if row[0] == scenario_id:
               row[1]  = 'Y';
               row[2]  = int_selected_count
               row[3]  = num_areasqkm;
               row[4]  = num_mean_score;
               row[5]  = num_solid_waste;
               row[6]  = num_liquid_waste;
               row[7]  = datetime.datetime.now();
               cursor.updateRow(row);
               break;

      util.write_stash({"scenario_id":scenario_id},aprx=aprx);

###############################################################################
class ExportSaveResults(object):

   #...........................................................................
   def __init__(self):

      self.label              = "T4 Export/Save Results";
      self.name               = "ExportSaveResults";
      self.description        = "Export/Save Results";
      self.canRunInBackground = False;

   #...........................................................................
   def getParameterInfo(self):
   
      #########################################################################
      parm_enb       = True;
      parm_frame     = False;
      scenarios      = [];
      def_scenario   = None;
      param1_columns = []
      param1_value   = None;
      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      if not arcpy.Exists(aprx.defaultGeodatabase + os.sep + util.g_scenario_fc):
         err_val  = "Scenario Storage has not been initialized.";
         err_enb  = True;
         parm_enb = False;
         parm_frame = False;
      
      else:
         try:
            aprx = arcpy.mp.ArcGISProject(util.g_prj);
            scenarios,def_scenario = util.fetchScenarioIDs(aprx=aprx);
            mapnames,def_mapname   = util.fetchMapNames(aprx=aprx);
            
            (param1_columns,param1_value) = util.fetchScenarioCharacteristics(
                scenario_id = def_scenario
               ,aprx        = aprx
            );
            
            if util.sniffEditingState(workspace=aprx.defaultGeodatabase):
               err_val = "Please save or delete all pending edits before proceeding.";
               err_enb = True;
            else:
               err_val = None;
               err_enb = False;
            
         except Exception as e:
            util.dzlog(str(sys.exc_info()),'error');
            raise;
         
      if len(scenarios) == 0:
         err_val  = "No scenarios found in system.";
         err_enb  = True;
         parm_enb = False;
         parm_frame = False;
         
      #########################################################################
      try:
         (
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
         ) = util.fetchReclassification(def_scenario,aprx);
         
      except Exception as e:
         util.dzlog(str(sys.exc_info()),'error');
         raise;
      
      #########################################################################
      param0 = arcpy.Parameter(
          displayName   = ""
         ,name          = "ErrorConditions"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = err_enb
      );
      param0.value = err_val;

      #########################################################################
      param1 = arcpy.Parameter(
          displayName   = ''
         ,name          = "ScenarioCharacteristics"
         ,datatype      = "GPValueTable"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_enb
         ,category      = "Scenario Characteristics"
      );
      param1.columns = param1_columns;
      param1.value   = param1_value;

      ##---------------------------------------------------------------------##
      param2 = arcpy.Parameter(
          displayName   = "Scenario ID"
         ,name          = "ScenarioID"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param2.filter.type = "ValueList";
      param2.filter.list = scenarios;
      param2.value       = def_scenario;

      #########################################################################
      param3 = arcpy.Parameter(
          displayName   = "Map Layout Graphic"
         ,name          = "MapLayoutGraphic"
         ,datatype      = "GPString"
         ,parameterType = "Required"
         ,direction     = "Input"
         ,enabled       = parm_enb
      );
      param3.value       = 'Disabled';
      param3.filter.type = "ValueList";
      ary_choices = ['Disabled'];
      lyts = aprx.listLayouts("*");
      for item in lyts:
         ary_choices.append(item.name);
      
      param3.filter.list = ary_choices;
      
      #########################################################################
      param4 = arcpy.Parameter(
          displayName   = "Map Layout Frame For Zoom"
         ,name          = "MapLayoutFrameForZoom"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_frame
      );
      ary_mfs = ['Disabled'];
      param4.value = 'Disabled';
      if param3.value != 'Disabled':
         lyt = aprx.listLayouts(param3.value)[0];
         mfs = lyt.listElements("mapframe_element","*");
         for item in mfs:
            ary_mfs.append(item.name);
            
         if len(ary_mfs) > 0:
            param4.value = ary_mfs[1];
            
      param4.filter.type = "ValueList";
      param4.filter.list = ary_mfs;
      
      #########################################################################
      param5 = arcpy.Parameter(
          displayName   = "Auto Zoom To Layer"
         ,name          = "AutoZoomToLayer"
         ,datatype      = "GPString"
         ,parameterType = "Optional"
         ,direction     = "Input"
         ,enabled       = parm_frame
      );
      ary_lyr = ['Disabled'];
      param5.value = 'Disabled';
      if param3.value != 'Disabled' and param4.value is not None:
         lyt  = aprx.listLayouts(param3.value)[0];
         mfs  = lyt.listElements("mapframe_element",param4.value);
         if len(mfs) > 0:
            lyrs = mfs[0].map.listLayers("*");
            
            for item in lyrs:
               ary_lyr.append(item.name);
               
               if item.name[-21:] == "_StagingSiteSelection":
                  param5.value = item.name;

            if len(lyrs) > 0 and param5.value is None:
               param5.value = lyrs[0].name;
               
      param5.filter.type = "ValueList";
      param5.filter.list = ary_lyr;
         
      #########################################################################
      param6 = arcpy.Parameter(
          displayName   = "Export File"
         ,name          = "ExportFile"
         ,datatype      = "DEFile"
         ,parameterType = "Required"
         ,direction     = "Output"
         ,enabled       = parm_enb
      );
      param6.filter.list = ['xlsx'];

      params = [
          param0
         ,param1
         ,param2
         ,param3
         ,param4
         ,param5
         ,param6
      ];

      return params;

   #...........................................................................
   def isLicensed(self):

      return True;

   #...........................................................................
   def updateParameters(self,parameters):

      if parameters[2].altered and not parameters[2].hasBeenValidated:
         aprx = arcpy.mp.ArcGISProject(util.g_prj);
         
         (columns,value) = util.fetchScenarioCharacteristics(
             scenario_id = parameters[2].value
            ,aprx        = aprx
         );
         
         parameters[1].value   = value;
      
      if parameters[3].altered and not parameters[3].hasBeenValidated:
      
         if parameters[3].valueAsText == 'Disabled':
            parameters[4].enabled = False;
            parameters[5].enabled = False;
            
         else:
            ary_mfs = [];
            parameters[4].enabled = True;
            parameters[5].enabled = True;
            aprx = arcpy.mp.ArcGISProject(util.g_prj);
            lyt  = aprx.listLayouts(parameters[3].valueAsText)[0];
            mfs  = lyt.listElements("mapframe_element","*");
            for item in mfs:
               ary_mfs.append(item.name);
               
            if len(ary_mfs) > 0:
               parameters[4].filter.list = ['Disabled'] + ary_mfs;
               parameters[4].value = ary_mfs[0];
               
               ary_lyr = [];
               ary_itm = [];
               mf = lyt.listElements("mapframe_element",parameters[4].valueAsText)[0];
               
               if mf is None or mf.map is None:
                  parameters[5].filter.list = ['Disabled'];
                  parameters[5].value = 'Disabled'
               
               else:
                  try:
                     lyrs = mf.map.listLayers("*");
                  except:
                     lyrs = [];
                  
                  for item in lyrs:
                     if item.name not in ['World Topographic Map','World Hillshade']:
                        ary_lyr.append(item.name);
                        ary_itm.append(item);
                     
                        if item.name[-12:] == "_WeightedSum":
                           parameters[5].value = item.name;

                  if len(ary_itm) > 0:
                     parameters[5].value = ary_itm[0].name;
                     
                  else:
                     parameters[5].value = 'Disabled';
                  
                  parameters[5].filter.list = ['Disabled'] + ary_lyr;
               
            else:
               parameters[4].filter.list = ['Disabled'];
               parameters[4].value = 'Disabled';
               parameters[5].filter.list = ['Disabled'];
               parameters[5].value = 'Disabled';
               
      elif parameters[4].altered and not parameters[4].hasBeenValidated:
      
         ary_lyr = [];
         ary_itm = [];
         aprx = arcpy.mp.ArcGISProject(util.g_prj);
         lyt  = aprx.listLayouts(parameters[3].valueAsText)[0];
         mfs  = lyt.listElements("mapframe_element",parameters[4].valueAsText);
         
         if len(mfs) > 0:
            try:
               lyrs = mfs[0].map.listLayers("*");
            except:
               lyrs = [];
               
            for item in lyrs:
               if item.name not in ['World Topographic Map','World Hillshade']:
                  ary_lyr.append(item.name);
                  ary_itm.append(item);
               
                  if item.name[-21:] == "_StagingSiteSelection":
                     parameters[5].value = item.name;

            if len(ary_itm) > 0:
               parameters[5].value = ary_itm[0].name;
               parameters[5].filter.list = ['Disabled'] + ary_lyr;
               
            else:
               parameters[5].value = 'Disabled';
               parameters[5].filter.list = ['Disabled'];
                  
         else:
            parameters[5].filter.list = ['Disabled'];
            parameters[5].value = 'Disabled';

   #...........................................................................
   def updateMessages(self,parameters):

      if  parameters[0].valueAsText is not None  \
      and parameters[0].valueAsText != "":
         parameters[0].setErrorMessage(parameters[0].valueAsText);
         
      return;

   #...........................................................................
   def execute(self,parameters,messages):
   
      #########################################################################
      # Step 10
      # Read the parameters
      #########################################################################
      util.dzlog('Starting the Export/Save Results process','debug',reset=True);
      scenario_id   = parameters[2].valueAsText;
      if scenario_id == "" or scenario_id == " ":
         scenario_id = None;
      lyt_settings  = parameters[3].value;
      mf_settings   = parameters[4].value;
      lyr_settings  = parameters[5].value;
      dest_filename = parameters[6].valueAsText;
      
      arcpy.env.overwriteOutput = True;
      aprx = arcpy.mp.ArcGISProject(util.g_prj);
      
      #########################################################################
      # Step 20
      # Initialize the workbook and summary sheet
      #########################################################################
      wb = openpyxl.Workbook();
      sum = wb.active;
      sum.title = 'Summary';
      sum['A1'] = "EPA Staging Siting Tool Summary"
      ft18 = openpyxl.styles.Font(size=18);
      bldu = openpyxl.styles.Font(bold=True,underline="single");
      bld  = openpyxl.styles.Font(bold=True);
      lft  = openpyxl.styles.Alignment(horizontal='left');
      rht  = openpyxl.styles.Alignment(horizontal='right');
      sum['A1'].font = ft18;
      
      row_sht = 2
      sum['A' + str(row_sht)].font = bld;
      sum['A' + str(row_sht)] = "Scenario ID";
      sum['B' + str(row_sht)] = scenario_id;
      
      sum.column_dimensions['A'].width  = 25;
      sum.column_dimensions['B'].width  = 20;
      sum.column_dimensions['C'].width  = 22;
      sum.column_dimensions['D'].width  = 15;
      sum.column_dimensions['E'].width  = 22;
      sum.column_dimensions['F'].width  = 22;
      sum.column_dimensions['G'].width  = 23;
      sum.column_dimensions['H'].width  = 10;
      
      #########################################################################
      # Step 30
      # Generate Map graphic for report
      #########################################################################
      if lyt_settings == 'Disabled':
         util.dzlog('Layout Graphic generation is disabled per user request.','debug');
         row_sht += 2;
         
      else:
         util.dzlog('Searching for Layout named ' + str(lyt_settings),'debug');
         lyt = aprx.listLayouts(lyt_settings)[0];
         
         if mf_settings is not None and mf_settings != "" and mf_settings != "Disabled":
            util.dzlog('Searching for Map Frame named ' + str(mf_settings),'debug');
            mf = lyt.listElements("mapframe_element",mf_settings)[0];
            
            if lyr_settings is not None and lyr_settings != "" and lyr_settings != "Disabled":
               util.dzlog('Searching for Layer on Map on Map Frame named ' + str(lyr_settings),'debug');
               lyr = mf.map.listLayers(lyr_settings)[0];
            
               ext  = mf.getLayerExtent(lyr,False,True);
               util.dzlog('Layer Extent [' + str(ext.XMin) + ',' + str(ext.YMin) + ',' + str(ext.XMax) + ',' + str(ext.YMax) + ']','debug');
               ext2 = util.buffer_extent(ext,0.05);
               util.dzlog('Buffered Extent [' + str(ext2.XMin) + ',' + str(ext2.YMin) + ',' + str(ext2.XMax) + ',' + str(ext2.YMax) + ']','debug');
               
               if math.isnan(ext2.XMin):
                  ext2 = ext;
               
               mf.camera.setExtent(ext2);
         
         map_image = arcpy.env.scratchFolder + os.sep + 'z' + scenario_id + '.png';
         util.dzlog('Exporting Pro Layout to ' + str(map_image),'debug');
         
         lyt.exportToPNG(
            out_png = map_image
         );
         
         from PIL import Image;
         # The PIL package will clutter up the tool log.
         # These statements will quieted things down. 
         # If you are having trouble with Pillow, comment out these statements to return to normal PIL logging
         pil_logger = logging.getLogger('PIL');
         pil_logger.setLevel(logging.INFO);
         
         baseheight = 567;
         img = Image.open(map_image);
         hpercent = (baseheight / float(img.size[1]));
         wsize = int((float(img.size[0]) * float(hpercent)));
         img = img.resize((wsize,baseheight),Image.LANCZOS);
         img.save(map_image);
         
         img = openpyxl.drawing.image.Image(
            map_image
         );
         
         img.width  = wsize;
         img.height = baseheight;
         img.anchor = 'C2';
         sum.add_image(img);
         
         row_sht += 30;
         
      #########################################################################
      # Step 40
      # List out the final results
      #########################################################################
      sum['A' + str(row_sht)].font = bldu;
      sum['A' + str(row_sht)] = "Name";
      sum['B' + str(row_sht)].font = bldu;
      sum['B' + str(row_sht)] = "Contaminant Type";
      sum['C' + str(row_sht)].font = bldu;
      sum['C' + str(row_sht)].alignment = rht;
      sum['C' + str(row_sht)] = "Mean Suitability Score";
      sum['D' + str(row_sht)].font = bldu;
      sum['D' + str(row_sht)].alignment = rht;
      sum['D' + str(row_sht)] = "Area (SqKm)";
      sum['E' + str(row_sht)].font = bldu;
      sum['E' + str(row_sht)].alignment = rht;
      sum['E' + str(row_sht)] = "Solid Waste Capacity (m3)";
      sum['F' + str(row_sht)].font = bldu;
      sum['F' + str(row_sht)].alignment = rht;
      sum['F' + str(row_sht)] = "Liquid Waste Capacity (L)";
      sum['G' + str(row_sht)].font = bldu;
      sum['G' + str(row_sht)].alignment = rht;
      sum['G' + str(row_sht)] = "Liquid Waste Capacity (m3)";
      sum['H' + str(row_sht)].font = bldu;
      sum['H' + str(row_sht)].alignment = rht;
      sum['H' + str(row_sht)] = "Notes";
      row_sht += 1;
      
      sitingstaging = os.path.join(
          aprx.defaultGeodatabase
         ,scenario_id + "_STAGINGSITESELECTION"
      );
      
      flds = [
          'name'
         ,'contamination_type'
         ,'MEAN_Suitability_Score'
         ,'SUM_areasqkm'
         ,'SUM_available_solid_waste_capacity_m3'
         ,'SUM_available_liquid_waste_capacity_L'
         ,'SUM_available_liquid_waste_capacity_m3'
         ,'FIRST_notes'
      ];
      
      with arcpy.da.SearchCursor(
          sitingstaging
         ,flds
      ) as cursor:
         for row in cursor:
            sum['A' + str(row_sht)] = row[0];
            sum['B' + str(row_sht)] = row[1];
            sum['C' + str(row_sht)] = row[2];
            sum['D' + str(row_sht)] = row[3];
            sum['E' + str(row_sht)] = row[4];
            sum['F' + str(row_sht)] = row[5];
            sum['G' + str(row_sht)] = row[6];
            sum['H' + str(row_sht)] = row[7];
            row_sht += 1;
            
      #########################################################################
      # Step 50
      # Write out the Scenario Characteristics 
      #########################################################################
      cdict = util.fetchScenarioCharacteristics_dict(
          scenario_id = scenario_id
         ,aprx        = aprx
      );
      row_sht += 3;
      
      sum['A' + str(row_sht)].font = bld;
      sum['A' + str(row_sht)] = "Scenario Characteristics";
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Area of Interest ID";
      sum['B' + str(row_sht)] = cdict["Area of Interest ID"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Slope Grid Size (m2)";
      sum['B' + str(row_sht)] = cdict["Slope Grid Size (m2)"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Land Cover Grid Size (m2)";
      sum['B' + str(row_sht)] = cdict["Land Cover Grid Size (m2)"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "NHD Grid Size (m2)";
      sum['B' + str(row_sht)] = cdict["NHD Grid Size (m2)"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Roads Grid Size (m2)";
      sum['B' + str(row_sht)] = cdict["Roads Grid Size (m2)"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "SSURGO Grid Size (m2)";
      sum['B' + str(row_sht)] = cdict["SSURGO Grid Size (m2)"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Slope Reclassification";
      sum['B' + str(row_sht)] = cdict["Slope Reclassification"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Land Cover Reclassification";
      sum['B' + str(row_sht)] = cdict["Land Cover Reclassification"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "NHD Reclassification";
      sum['B' + str(row_sht)] = cdict["NHD Reclassification"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Roads Reclassification";
      sum['B' + str(row_sht)] = cdict["Roads Reclassification"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "SSURGO Reclassification";
      sum['B' + str(row_sht)] = cdict["SSURGO Reclassification"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Slope Weight Factor";
      sum['B' + str(row_sht)] = cdict["Slope Weight Factor"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Land Cover Weight Factor";
      sum['B' + str(row_sht)] = cdict["Land Cover Weight Factor"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "NHD Weight Factor";
      sum['B' + str(row_sht)] = cdict["NHD Weight Factor"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Roads Weight Factor";
      sum['B' + str(row_sht)] = cdict["Roads Weight Factor"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "SSURGO Weight Factor";
      sum['B' + str(row_sht)] = cdict["SSURGO Weight Factor"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Selected Feature Count";
      sum['B' + str(row_sht)] = cdict["Selected Feature Count"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Selected Total Area (sqkm)";
      sum['B' + str(row_sht)] = cdict["Selected Total Area (sqkm)"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Username";
      sum['B' + str(row_sht)] = cdict["Username"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Date Created";
      sum['B' + str(row_sht)] = cdict["Date Created"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Date Last Updated";
      sum['B' + str(row_sht)] = cdict["Date Last Updated"];
      row_sht += 1;
      
      sum['A' + str(row_sht)] = "Notes";
      sum['B' + str(row_sht)] = cdict["Notes"];
      row_sht += 1;
      
      #########################################################################
      # Step 60
      # Write out the selected parcels sheet
      #########################################################################
      sht = wb.create_sheet('Selected');
      
      sht.column_dimensions['A'].width  = 15;
      sht.column_dimensions['B'].width  = 15;
      sht.column_dimensions['C'].width  = 22;
      sht.column_dimensions['D'].width  = 20;
      sht.column_dimensions['E'].width  = 15;
      sht.column_dimensions['F'].width  = 22;
      sht.column_dimensions['G'].width  = 22;
      sht.column_dimensions['H'].width  = 23;
      sht.column_dimensions['I'].width  = 15;
      row_sht = 1;
      
      sht['A' + str(row_sht)].font = bldu;
      sht['A' + str(row_sht)] = "ID";
      sht['B' + str(row_sht)].font = bldu;
      sht['B' + str(row_sht)] = "Name";
      sht['C' + str(row_sht)].font = bldu;
      sht['C' + str(row_sht)] = "Contaminant Type";
      sht['D' + str(row_sht)].font = bldu;
      sht['D' + str(row_sht)].alignment = rht;
      sht['D' + str(row_sht)] = "Mean Suitability Score";
      sht['E' + str(row_sht)].font = bldu;
      sht['E' + str(row_sht)].alignment = rht;
      sht['E' + str(row_sht)] = "Area (SqKm)";
      sht['F' + str(row_sht)].font = bldu;
      sht['F' + str(row_sht)].alignment = rht;
      sht['F' + str(row_sht)] = "Solid Waste Capacity (m3)";
      sht['G' + str(row_sht)].font = bldu;
      sht['G' + str(row_sht)].alignment = rht;
      sht['G' + str(row_sht)] = "Liquid Waste Capacity (L)";
      sht['H' + str(row_sht)].font = bldu;
      sht['H' + str(row_sht)].alignment = rht;
      sht['H' + str(row_sht)] = "Liquid Waste Capacity (m3)";
      sht['I' + str(row_sht)].font = bldu;
      sht['I' + str(row_sht)].alignment = rht;
      sht['I' + str(row_sht)] = "Notes";
      row_sht += 1;
      
      sitingstaging = os.path.join(
          aprx.defaultGeodatabase
         ,scenario_id + "_SELECTED"
      );
      
      flds = [
          'id'
         ,'name'
         ,'contamination_type'
         ,'suitability_score'
         ,'areasqkm'
         ,'available_solid_waste_capacity_m3'
         ,'available_liquid_waste_capacity_L'
         ,'available_liquid_waste_capacity_m3'
         ,'notes'
      ];
      
      with arcpy.da.SearchCursor(
          in_table    = sitingstaging
         ,field_names = flds
         ,sql_clause  = (None,'ORDER BY name,contamination_type,id')
      ) as cursor:
         for row in cursor:
            sht['A' + str(row_sht)] = row[0];
            sht['B' + str(row_sht)] = row[1];
            sht['C' + str(row_sht)] = row[2];
            sht['D' + str(row_sht)] = row[3];
            sht['E' + str(row_sht)] = row[4];
            sht['F' + str(row_sht)] = row[5];
            sht['G' + str(row_sht)] = row[6];
            sht['H' + str(row_sht)] = row[7];
            sht['I' + str(row_sht)] = row[8];
            row_sht += 1;

      #########################################################################
      # Step 70
      # Write out the excel file
      #########################################################################
      wb.save(dest_filename);      
      
      util.write_stash({"scenario_id":scenario_id},aprx=aprx);
      
  