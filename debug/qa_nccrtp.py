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
# Short circuit the toolbox and load the util toolbox 
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
default_map = aprx.listMaps('*')[0];
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
print("Step 70: Create expanded AOI.");
coordinates = [
    (-78.955081122394304,35.848796313402339)
   ,(-78.930173667091736,35.813498807849165)
   ,(-78.810146200932579,35.784527341462606)
   ,(-78.762705724414644,35.848854031422682)
   ,(-78.780763271189443,35.913892136832359)
   ,(-78.865193673011461,35.940071018982181)
   ,(-78.945870430313093,35.919231338766117)
   ,(-78.955081122394304,35.848796313402339)
];

temp_nccrtp = commonqa.temp_aoi(
    coordinates = coordinates
   ,temp_name   = "temp_nccrtp"
);

###############################################################################
# Step 80
# Add new Areas of Interest
###############################################################################
print("Step 80: Add new Area of Interest."); 
st = util_sideloaded.LoadNewAOI();
parameters = st.getParameterInfo();
parameters[1].value  = 'NCCRTP';
parameters[2].value  = None;
parameters[3].value  = temp_nccrtp;
parameters[5].value  = ed['slope'];
parameters[6].value  = ed['landcover'];
parameters[7].value  = ed['nhd'];
parameters[8].value  = ed['roads'];
parameters[9].value  = ed['ssurgo'];
parameters[10].value = 5;
parameters[11].value = 'National Computing Center RTP';
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 90
# Clear all scenarios
###############################################################################
print("Step 90: Scenario Setup."); 
st = util_sideloaded.ScenarioSetup();
parameters = st.getParameterInfo();
parameters[1].value = True;
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 100
# Add new Scenarios
###############################################################################
print("Step 100: Add new scenario."); 
st = util_sideloaded.LoadNewScenario();
parameters = st.getParameterInfo();
parameters[1].value  = 'NCCRTP1';
parameters[2].value  = 'NCCRTP';
parameters[3].value  = True;
parameters[4].value  = True;
parameters[5].value  = True;
parameters[6].value  = util.g_default_nhdgridsize;
parameters[7].value  = True;
parameters[8].value  = util.g_default_tnmroadsgridsize;
parameters[9].value  = True;
parameters[10].value = util.g_default_ssurgogridsize;
parameters[11].value = 'Comanche Expanded Scenario';
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 110
# Run ConfirmSuitabilityCriteria
###############################################################################
print("Step 120: Run ConfirmSuitabilityCriteria.");
st = tool_sideloaded.ConfirmSuitabilityCriteria();
parameters = st.getParameterInfo();
parameters[2].value  = 'NCCRTP1';
parameters[3].value  = default_map.name;
parameters[4].value  = "Value > 10";
parameters[5].value  = "Value = 11 OR Value = 23 OR Value = 24 OR Value = 41 OR Value = 42 OR Value = 43 OR Value = 81 OR Value = 82 OR Value = 90 OR Value = 95";
parameters[6].value  = "Value <= 500";
parameters[7].value  = "Value < 200 OR Value > 500";
parameters[8].value  = "hydgrpdcd = 'B' OR hydgrpdcd = 'B/D' OR hydgrpdcd = 'A' OR hydgrpdcd = 'A/D' OR hydgrpdcd = ' '";
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 120
# Run SpecifyCriteriaWeight
###############################################################################
print("Step 130: Run SpecifyCriteriaWeight."); 
st = tool_sideloaded.SpecifyCriteriaWeight();
parameters = st.getParameterInfo();
parameters[2].value  = 'NCCRTP1';
parameters[3].value  = default_map.name;
parameters[4].value  = "1";
parameters[5].value  = "1";
parameters[6].value  = "1";
parameters[7].value  = "1";
parameters[8].value  = "1";
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 130
# Fake a layer selection and run FinalizeStagingParcelSelection
###############################################################################
print("Step 140: Run FinalizeStagingParcelSelection for expanded."); 
coordinates = [
    (-78.866385725252968,35.875186468910918)
   ,(-78.868376220032658,35.882448425840792)
   ,(-78.872886179251807,35.890522971480642)
   ,(-78.889274423141984,35.891592069035873)
   ,(-78.888186312708442,35.873691274519118)
   ,(-78.866385725252968,35.875186468910918)
];
lyr_expanded = commonqa.make_selection_by_coords(
    coordinates   = coordinates
   ,input_dataset = 'NCCRTP1_WEIGHTEDSUM'
   ,lyr_name      = 'NCCRTP1_lyrtmp'
   ,srid          = 4269
);

st = tool_sideloaded.FinalizeStagingParcelSelection();
parameters = st.getParameterInfo();
parameters[2].value  = 'NCCRTP1';
parameters[3].value  = default_map.name;
parameters[4].value  = lyr_expanded;
parameters[5].value  = True;
messages = None;
rez = st.execute(parameters,messages);

###############################################################################
# Step 140
# Run ExportSaveResults
###############################################################################
print("Step 160: Run ExportSaveResults."); 
if arcpy.Exists(arcpy.env.scratchFolder + os.sep + 'NCCRTP1.xlsx'):
   arcpy.Delete_management(arcpy.env.scratchFolder + os.sep + 'NCCRTP1.xlsx');   
st = tool_sideloaded.ExportSaveResults();
parameters = st.getParameterInfo();
parameters[2].value  = 'NCCRTP1';
parameters[3].value  = 'Disabled';
parameters[6].value  = arcpy.env.scratchFolder + os.sep + 'NCCRTP1.xlsx'
messages = None;
rez = st.execute(parameters,messages);

print("\nqa_nccrtp complete.");

