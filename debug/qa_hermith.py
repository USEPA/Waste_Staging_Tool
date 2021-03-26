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
# Locate the Essential Datasets
###############################################################################
ed = commonqa.search_ed();
  
if not arcpy.Exists(ed['slope']):
   raise Exception("Essential Data Slope input not found.");
   
if not arcpy.Exists(ed['landcover']):
   raise Exception("Essential Data Landcover input not found.");
   
if not arcpy.Exists(ed['nhd']):
   raise Exception("Essential Data NHD input not found.");
   
if not arcpy.Exists(ed['roads']):
   raise Exception("Essential Data Roads input not found.");
   
if not arcpy.Exists(ed['ssurgo']):
   raise Exception("Essential Data SSurgo input not found.");

print("Step 20: Found all ED components");

###############################################################################
# Step 30
# Short circuit the toolbox and load the util toolbox directly in order to 
# access the parameters.  ArcPy remains a buggy mess and these contortions are
# the only way I can test the tools without just recreating steps from scratch
###############################################################################
toolbx = os.path.join(util.g_pn,"EPA-Storage-Staging-Site-Util.pyt");
print("Step 30: Sideloading util toolbox from \n   " + toolbx);
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
# Step 40
# Short circuit the toolbox and load the tool toolbox
###############################################################################
toolbx = os.path.join(util.g_pn,"EPA-Storage-Staging-Site-Tool.pyt");
print("Step 40: Sideloading tool toolbox from \n   " + toolbx);
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
# Step 50
# Set project common variables
###############################################################################
print("Step 50: Loading workspace and project.")
wrksp = os.path.join(util.g_pn,"EPA-Storage-Staging-Site-Tool.gdb");
arcpy.env.workspace = wrksp;
print("   workspace: " + str(wrksp));
arcpy.env.scratchWorkspace = os.path.join(util.g_pn,"scratch.gdb");
arcpy.env.overwriteOutput = True;
aprx = arcpy.mp.ArcGISProject(util.g_prj);
print("   project: " + str(aprx.filePath));

if not arcpy.Exists(aprx.defaultGeodatabase):
   arcpy.CreateFileGDB_management(
       out_folder_path = util.g_pn
      ,out_name        = "EPA-Storage-Staging-Site-Tool.gdb"
   );

###############################################################################
# Step 60
# Clear all AOIs
###############################################################################
print("Step 60: Execute AOI Setup."); 
st = util_sideloaded.AOISetup();
parameters = st.getParameterInfo();
parameters[1].value = True;
parameters[2].value = True;
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 70
# Create Area of Interest fc
###############################################################################
print("Step 70: Execute AOI Creation.");
coordinates = [
    (-90.56545257568358,43.18302464679583)
   ,(-90.43052673339844,43.17914423586488)
   ,(-90.41885375976562,43.224191874050916)
   ,(-90.43069839477539,43.282704074896195)
   ,(-90.5958366394043,43.277330299293055)
   ,(-90.59429168701172,43.18527767545014)
   ,(-90.56545257568358,43.18302464679583)
];

temp_aoi = commonqa.temp_aoi(
    coordinates = coordinates
   ,temp_name   = "temp_aoi"
);

###############################################################################
# Step 80
# Add new Area of Interest
###############################################################################
print("Step 80: Add new Area of Interest."); 
st = util_sideloaded.LoadNewAOI();
parameters = st.getParameterInfo();
parameters[1].value  = 'EagleCave';
parameters[2].value  = None;
parameters[3].value  = temp_aoi;
parameters[5].value  = ed['slope'];
parameters[6].value  = ed['landcover'];
parameters[7].value  = ed['nhd'];
parameters[8].value  = ed['roads'];
parameters[9].value  = ed['ssurgo'];
parameters[10].value = 5;
parameters[11].value = 'test aoi, please delete';
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 90
# Rename Area of Interest
###############################################################################
print("Step 90: Rename Area of Interest."); 
st = util_sideloaded.RenameAOI();
parameters = st.getParameterInfo();
parameters[1].value = 'EagleCave';
parameters[2].value = 'HermitHole';
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 100
# Delete Area of Interest
###############################################################################
print("Step 100: Delete Area of Interest."); 
st = util_sideloaded.DeleteAOI();
parameters = st.getParameterInfo();
parameters[1].value = 'HermitHole';
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 110
# Add new Area of Interest
###############################################################################
print("Step 110: Read Area of Interest."); 
st = util_sideloaded.LoadNewAOI();
parameters = st.getParameterInfo();
parameters[1].value  = 'EagleCave';
parameters[2].value  = None;
parameters[3].value  = temp_aoi;
parameters[5].value  = ed['slope'];
parameters[6].value  = ed['landcover'];
parameters[7].value  = ed['nhd'];
parameters[8].value  = ed['roads'];
parameters[9].value  = ed['ssurgo'];
parameters[10].value = 5;
parameters[11].value = 'test aoi, please delete';
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 120
# Clear all scenarios
###############################################################################
print("Step 120: Scenario Setup."); 
st = util_sideloaded.ScenarioSetup();
parameters = st.getParameterInfo();
parameters[1].value = True;
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 130
# Add new Scenario
###############################################################################
print("Step 130: Add new scenario."); 
st = util_sideloaded.LoadNewScenario();
parameters = st.getParameterInfo();
parameters[1].value  = 'EagleCave1';
parameters[2].value  = 'EagleCave';
parameters[3].value  = True;
parameters[4].value  = True;
parameters[5].value  = True;
parameters[6].value  = util.g_default_nhdgridsize;
parameters[7].value  = True;
parameters[8].value  = util.g_default_tnmroadsgridsize;
parameters[9].value  = True;
parameters[10].value = util.g_default_ssurgogridsize;
parameters[11].value = 'test scenario, please delete';
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 140
# Duplicate Scenario
###############################################################################
print("Step 140: Duplicate scenario."); 
st = util_sideloaded.DuplicateScenario();
parameters = st.getParameterInfo();
parameters[1].value  = 'EagleCave1';
parameters[2].value  = 'EagleCave99';
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 150
# Rename Scenario
###############################################################################
print("Step 150: Rename scenario."); 
st = util_sideloaded.RenameScenario();
parameters = st.getParameterInfo();
parameters[1].value  = 'EagleCave99';
parameters[2].value  = 'HermitHole';
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 160
# Delete Scenario
###############################################################################
print("Step 160: Delete scenario."); 
st = util_sideloaded.DeleteScenario();
parameters = st.getParameterInfo();
parameters[1].value  = 'HermitHole';
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 170
# Run ConfirmSuitabilityCriteria
###############################################################################
print("Step 170: Run ConfirmSuitabilityCriteria.");
default_map = aprx.listMaps('*')[0];
st = tool_sideloaded.ConfirmSuitabilityCriteria();
parameters = st.getParameterInfo();
parameters[2].value  = 'EagleCave1';
parameters[3].value  = default_map.name;
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 180
# Run SpecifyCriteriaWeight
###############################################################################
print("Step 180: Run SpecifyCriteriaWeight."); 
st = tool_sideloaded.SpecifyCriteriaWeight();
parameters = st.getParameterInfo();
parameters[2].value  = 'EagleCave1';
parameters[3].value  = default_map.name;
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 190
# Fake a layer selection
###############################################################################
print("Step 190: Make selection against weighted sum.");
lyr_eaglecave = commonqa.make_selection_by_attr(
    where_clause = '"suitability_score" = 1'
   ,input_dataset = 'EagleCave1_WEIGHTEDSUM'
   ,lyr_name      = 'EagleCave1_lyrtmp'
);

###############################################################################
# Step 200
# Run FinalizeStagingParcelSelection
###############################################################################
print("Step 200: Run FinalizeStagingParcelSelection."); 
st = tool_sideloaded.FinalizeStagingParcelSelection();
parameters = st.getParameterInfo();
parameters[2].value  = 'EagleCave1';
parameters[3].value  = default_map.name;
parameters[4].value  = lyr_eaglecave;
parameters[5].value  = True;
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 210
# Run ExportSaveResults
###############################################################################
if arcpy.Exists(arcpy.env.scratchFolder + os.sep + 'EagleCave1.xlsx'):
   arcpy.Delete_management(arcpy.env.scratchFolder + os.sep + 'EagleCave1.xlsx');
   
print("Step 210: Run ExportSaveResults."); 
st = tool_sideloaded.ExportSaveResults();
parameters = st.getParameterInfo();
parameters[2].value  = 'EagleCave1';
parameters[3].value  = 'Disabled';
parameters[6].value  = arcpy.env.scratchFolder + os.sep + 'EagleCave1.xlsx'
messages = None;
rez = st.execute(parameters,messages);

print("\nqa_hermith complete."); 

