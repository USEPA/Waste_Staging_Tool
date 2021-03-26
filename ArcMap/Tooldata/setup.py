import os;
import zipfile;
import arcpy;

pwd = os.path.dirname(os.path.realpath(__file__));

if arcpy.Exists(pwd + os.sep + "ModelInputTables.gdb"):
   arcpy.Delete_management(pwd + os.sep + "ModelInputTables.gdb");
   
with zipfile.ZipFile(pwd + os.sep + "ToolData.zip",'r') as zip_ref:
   zip_ref.extractall(pwd);
   
if arcpy.Exists(pwd + os.sep + "ModelOutputTables.gdb"):
   arcpy.Delete_management(pwd + os.sep + "ModelOutputTables.gdb");
   
arcpy.CreateFileGDB_management(pwd,"ModelOutputTables.gdb");
   
if arcpy.Exists(pwd + os.sep + ".." + os.sep + "Scratch" + os.sep + "Scratch.gdb"):
   arcpy.Delete_management(pwd + os.sep + ".." + os.sep + "Scratch" + os.sep + "Scratch.gdb");
   
if not os.path.exists(pwd + os.sep + ".." + os.sep + "Scratch"):
   os.mkdir(pwd + os.sep + ".." + os.sep + "Scratch");
   
arcpy.CreateFileGDB_management(pwd + os.sep + ".." + os.sep + "Scratch","Scratch.gdb");
   
