import arcpy,os,sys;
from importlib.util import spec_from_loader, module_from_spec;
from importlib.machinery import SourceFileLoader;
import commonqa;

if arcpy.CheckExtension("Spatial") == "Available":
   arcpy.CheckOutExtension("Spatial");
else:
   raise Exception('Spatial Analysis Extension not available.');
print("");

###############################################################################
# Step 10
# Add project path to python path and import util forcing project to aprx file
###############################################################################
project_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)));
print("Step 10: Importing utilities from project at \n   " + project_root + os.sep + "util.py");
sys.path.append(project_root);
import util;
util.g_prj = util.g_pn + os.sep + "EPA-Storage-Staging-Site-Tool.aprx";

###############################################################################
# Step 20
# Short circuit the toolbox and load the util toolbox directly in order to 
# access the parameters.  ArcPy remains a buggy mess and these contortions are
# the only way I can test the tools without just recreating steps from scratch
###############################################################################
toolbx = os.path.join(util.g_pn,"EPA-Storage-Staging-Site-Util.pyt");
print("Step 20: Sideloading util toolbox from \n   " + toolbx);
spec = spec_from_loader(
    'util_sideloaded'
   ,SourceFileLoader(
       'util_sideloaded'
      ,toolbx
   )
);
module = module_from_spec(spec);
spec.loader.exec_module(module);
sys.modules['util_sideloaded'] = module;
import util_sideloaded;
util.g_prj = util.g_pn + os.sep + "EPA-Storage-Staging-Site-Tool.aprx";

###############################################################################
# Step 30
# Short circuit the toolbox and load the tool toolbox
###############################################################################
toolbx = os.path.join(util.g_pn,"EPA-Storage-Staging-Site-Tool.pyt");
print("Step 30: Sideloading tool toolbox from \n   " + toolbx);
spec = spec_from_loader(
    'tool_sideloaded'
   ,SourceFileLoader(
       'tool_sideloaded'
      ,toolbx
   )
);
module = module_from_spec(spec);
spec.loader.exec_module(module);
sys.modules['tool_sideloaded'] = module;
import tool_sideloaded;
util.g_prj = util.g_pn + os.sep + "EPA-Storage-Staging-Site-Tool.aprx";

###############################################################################
# Step 40
# Set project common variables
###############################################################################
print("Step 40: Loading workspace and project.")
wrksp = os.path.join(util.g_pn,"EPA-Storage-Staging-Site-Tool.gdb");
arcpy.env.workspace = wrksp;
print("   workspace: " + str(wrksp));
arcpy.env.scratchWorkspace = os.path.join(util.g_pn,"scratch.gdb");
arcpy.env.overwriteOutput = True;
aprx = arcpy.mp.ArcGISProject(util.g_prj);
default_map = aprx.listMaps('*')[0];
print("   project: " + str(aprx.filePath));

if not arcpy.Exists(aprx.defaultGeodatabase):
   arcpy.CreateFileGDB_management(
       out_folder_path = util.g_pn
      ,out_name        = "EPA-Storage-Staging-Site-Tool.gdb"
   );

###############################################################################
# Step 50
# Clear all scenarios
###############################################################################
print("Step 50: Scenario Setup."); 
st = util_sideloaded.ScenarioSetup();
parameters = st.getParameterInfo();
parameters[1].value = False;
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 60
# Add new Scenario if not preexisting
###############################################################################
if not util.scenarioIDExists(
    id   = 'NewMunster1'
   ,aprx = None
):
   print("Step 60: Add new scenario."); 
   st = util_sideloaded.LoadNewScenario();
   parameters = st.getParameterInfo();
   parameters[1].value  = 'NewMunster1';
   parameters[2].value  = 'NewMunster';
   parameters[3].value  = True;
   parameters[4].value  = True;
   parameters[5].value  = True;
   parameters[6].value  = util.g_default_nhdgridsize;
   parameters[7].value  = True;
   parameters[8].value  = util.g_default_tnmroadsgridsize;
   parameters[9].value  = True;
   parameters[10].value = util.g_default_ssurgogridsize;
   parameters[11].value = 'test scenario';
   messages = None;
   rez = st.execute(parameters,messages);

###############################################################################
# Step 70
# Run ConfirmSuitabilityCriteria
###############################################################################
print("Step 70: Run ConfirmSuitabilityCriteria.");
st = tool_sideloaded.ConfirmSuitabilityCriteria();
parameters = st.getParameterInfo();
parameters[2].value  = 'NewMunster1';
parameters[3].value  = default_map.name;
parameters[4].value  = "Value > 10";
parameters[5].value  = "Value = 11 OR Value = 23 OR Value = 24 OR Value = 41 OR Value = 42 OR Value = 43 OR Value = 81 OR Value = 82 OR Value = 90 OR Value = 95";
parameters[6].value  = "Value <= 500";
parameters[7].value  = "Value < 200 OR Value > 500";
parameters[8].value  = "hydgrpdcd = 'B' OR hydgrpdcd = 'B/D' OR hydgrpdcd = 'A' OR hydgrpdcd = 'A/D' OR hydgrpdcd = ' '";
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 80
# Run SpecifyCriteriaWeight
###############################################################################
print("Step 80: Run SpecifyCriteriaWeight."); 
st = tool_sideloaded.SpecifyCriteriaWeight();
parameters = st.getParameterInfo();
parameters[2].value  = 'NewMunster1';
parameters[3].value  = default_map.name;
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 90
# Fake a layer selection
###############################################################################
print("Step 90: Make selection using a bounding box.");
coordinates = [
    (-88.163192,42.600514)
   ,(-88.118496,42.586283)
   ,(-88.127011,42.529928)
   ,(-88.190187,42.534740)
   ,(-88.163192,42.600514)
];

lyr_newmunster = commonqa.make_selection_by_coords(
    coordinates   = coordinates
   ,input_dataset = 'NewMunster1_WEIGHTEDSUM'
   ,lyr_name      = 'NewMunster1_lyrtmp'
   ,srid          = 4269
);

###############################################################################
# Step 100
# Run FinalizeStagingParcelSelection
###############################################################################
print("Step 100: Run FinalizeStagingParcelSelection."); 
st = tool_sideloaded.FinalizeStagingParcelSelection();
parameters = st.getParameterInfo();
parameters[2].value  = 'NewMunster1';
parameters[3].value  = default_map.name;
parameters[4].value  = lyr_newmunster;
parameters[5].value  = True;
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 110
# Run ExportSaveResults
###############################################################################
if arcpy.Exists(arcpy.env.scratchFolder + os.sep + 'NewMunster1.xlsx'):
   arcpy.Delete_management(arcpy.env.scratchFolder + os.sep + 'NewMunster1.xlsx');
   
print("Step 210: Run ExportSaveResults."); 
st = tool_sideloaded.ExportSaveResults();
parameters = st.getParameterInfo();
parameters[2].value  = 'NewMunster1';
parameters[3].value  = 'Disabled';
parameters[6].value  = arcpy.env.scratchFolder + os.sep + 'NewMunster1.xlsx'
messages = None;
rez = st.execute(parameters,messages);

print("\nqa_newmunster complete."); 

