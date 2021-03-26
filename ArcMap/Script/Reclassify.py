# Name: 2 Reclassify
# Description: Reclassify rasters as part of the Staging Site Selection Model
# Requirements: Spatial Analyst Extension

# Import system modules
import arcpy, os
from arcpy import env
from arcpy.sa import *

arcpy.env.overwriteOutput = True

# Define root directory and define geodatabase name
folder = os.path.dirname(arcpy.mapping.MapDocument('CURRENT').filePath)
Tooldata = os.path.join(folder, "Tooldata")
geodatabase = os.path.join(Tooldata, "ModelOutputTables.gdb")

# Set environment settings
#env.workspace = ""

# Set local variables
inSlope = Raster(os.path.join(geodatabase, "Extract_Slope"))
inRoads = Raster(os.path.join(geodatabase, "Extract_Roads"))
inSSURGO = Raster(os.path.join(geodatabase, "Extract_SSURGO"))
inNHD = Raster(os.path.join(geodatabase, "Extract_NHD"))
inLAND = Raster(os.path.join(geodatabase, "Extract_LAND"))
inTrueRaster = 0
inFalseConstant = 1

#SQL statements
#whereClause = "Value > 10" #Slope
#whereClause = "Value < 200 OR Value > 500" #Roads
#whereClause = "hydgrpdcd = 'B' OR hydgrpdcd = 'B/D' OR hydgrpdcd = 'A' OR hydgrpdcd = 'A/D' OR hydgrpdcd = ' '" #SSURGO
#whereClause = "Value <= 500" #NHD
#whereClause = "Value = 11 OR Value = 23 OR Value = 24 OR Value = 41 OR Value = 42 OR Value = 43 OR Value = 81 OR Value = 82 OR Value = 90 OR Value = 95" #Land

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Execute Con
arcpy.AddMessage("Processing Slope...")
outCon = Con(inSlope, inTrueRaster, inFalseConstant, sys.argv[2])
arcpy.AddMessage("Processing Roads...")
outCon2 = Con(inRoads, inTrueRaster, inFalseConstant, sys.argv[1])
arcpy.AddMessage("Processing Soils...")
outCon3 = Con(inSSURGO, inTrueRaster, inFalseConstant, sys.argv[4])
arcpy.AddMessage("Processing Surface Water...")
outCon4 = Con(inNHD, inTrueRaster, inFalseConstant, sys.argv[5])
arcpy.AddMessage("Processing Land Classification...")
outCon5 = Con(inLAND, inTrueRaster, inFalseConstant, sys.argv[3])

arcpy.AddMessage("Saving outputs...")

# Save the outputs 
outCon.save(os.path.join(geodatabase, "Reclass_Slope"))
outCon2.save(os.path.join(geodatabase, "Reclass_Roads"))
outCon3.save(os.path.join(geodatabase, "Reclass_SSURGO"))
outCon4.save(os.path.join(geodatabase, "Reclass_NHD"))
outCon5.save(os.path.join(geodatabase, "Reclass_LAND"))

arcpy.AddMessage("Done!")
