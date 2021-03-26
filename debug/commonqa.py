import arcpy,os,sys;
project_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)));
sys.path.append(project_root);
import util;

###############################################################################
def search_ed():
   
   slope = r"E:\SitingStagingCache\NED13\final\slope_conus_102010.img";
   if not arcpy.Exists(slope):
      slope = r"G:\SitingStagingCache\NED13\final\slope_conus_102010.img";
      
   landcover = r"E:\SitingStagingCache\NLCD2016\final\NLCD_2016_conus_102010.img";
   if not arcpy.Exists(landcover):
      landcover = r"E:\SitingStagingCache\NLCD\final\NLCD_2016_conus_102010.img";
   if not arcpy.Exists(landcover):
      landcover = r"G:\SitingStagingCache\NLCD2016\final\NLCD_2016_conus_102010.img";

   nhd = r"E:\SitingStagingCache\NHD\final\NHD_conus_102010.gdb\NHDPolygons_conus_102010";
   if not arcpy.Exists(nhd):
      nhd = r"E:\SitingStagingCache\NHD\final\NHD_conus.gdb\NHDPolygons_conus_102010";
   if not arcpy.Exists(nhd):
      nhd = r"G:\SitingStagingCache\NHD\final\NHD_conus_102010.gdb\NHDPolygons_conus_102010";

   roads = r"E:\SitingStagingCache\USGSTNM\final\TNMT_conus_102010.gdb\ROADS_conus_201020";
   if not arcpy.Exists(roads):
      roads = r"G:\SitingStagingCache\USGSTNM\final\TNMT_conus_102010.gdb\ROADS_conus_201020";

   ssurgo = r"E:\SitingStagingCache\EsriSSURGO\final\EsriSSURGO_conus_102010.gdb\EsriSSURGO_conus_102010";
   if not arcpy.Exists(ssurgo):
      ssurgo = r"G:\SitingStagingCache\EsriSSURGO\final\EsriSSURGO_conus_102010.gdb\EsriSSURGO_conus_102010";
      
   return {
       'slope'    : slope
      ,'landcover': landcover
      ,'nhd'      : nhd
      ,'roads'    : roads
      ,'ssurgo'   : ssurgo
   };
   
###############################################################################
def coords2fc(
    coordinates
   ,flds
   ,srid        = None
   ,temp_name   = None
):

   if temp_name is None:
      temp_name = "temp_aoi";
      
   if srid is None:
      sr = arcpy.SpatialReference(4269);  
   else:
      sr = arcpy.SpatialReference(srid);
      
   if arcpy.Exists(arcpy.env.scratchWorkspace + os.sep + temp_name):
      arcpy.Delete_management(arcpy.env.scratchWorkspace + os.sep + temp_name);
      
   arcpy.CreateFeatureclass_management(
       out_path          = arcpy.env.scratchWorkspace
      ,out_name          = temp_name
      ,geometry_type     = "POLYGON"
      ,has_m             = "DISABLED"
      ,has_z             = "DISABLED"
      ,spatial_reference = sr
      ,config_keyword    = None
   );
   
   if flds is not None:
      arcpy.management.AddFields(
          arcpy.env.scratchWorkspace + os.sep + temp_name
         ,[flds]
      );
   
   return temp_name;
   
###############################################################################
def temp_aoi(
    coordinates
   ,srid        = None
   ,temp_name   = None
   ,aoi_name    = None
):

   if aoi_name is None:
      aoi_name = 'aoi';
      
   temp_name = coords2fc(
       coordinates = coordinates
      ,flds        = ['aoi_name','TEXT','Area of Interest Name' ,255, None,'']
      ,srid        = srid
      ,temp_name   = temp_name
   );
   
   with arcpy.da.InsertCursor(
       arcpy.env.scratchWorkspace + os.sep + temp_name
      ,['aoi_name','SHAPE@']
   ) as cursor:
      cursor.insertRow([aoi_name,coordinates]);

   return arcpy.env.scratchWorkspace + os.sep + temp_name;
   
###############################################################################
def make_selection_by_attr(
    where_clause
   ,input_dataset
   ,lyr_name
):

   if arcpy.Exists(lyr_name):
      arcpy.Delete_management(lyr_name);
   
   arcpy.MakeFeatureLayer_management(
       in_features = input_dataset
      ,out_layer   = lyr_name
   );

   rez = arcpy.SelectLayerByAttribute_management(
       in_layer_or_view = lyr_name
      ,selection_type   = 'NEW_SELECTION'
      ,where_clause     = where_clause
   );
   
   return lyr_name;
   
###############################################################################
def make_selection_by_coords(
    coordinates
   ,input_dataset
   ,lyr_name
   ,srid         = None
):

   slicer = temp_aoi(
       coordinates = coordinates
      ,srid        = srid
      ,temp_name   = "slicer"
   );
   
   if arcpy.Exists(lyr_name):
      arcpy.Delete_management(lyr_name);
   
   arcpy.MakeFeatureLayer_management(
       in_features = input_dataset
      ,out_layer   = lyr_name
   );

   rez = arcpy.SelectLayerByLocation_management(
       in_layer         = lyr_name
      ,overlap_type     = 'INTERSECT'
      ,select_features  = slicer
      ,selection_type   = 'NEW_SELECTION'
   );
   
   return lyr_name;
   
   