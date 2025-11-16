.. _arch-interaction:

Interaction with pwrforge
=======================

pwrforge and other software
-------------------------

.. uml::

   !include pwrforge_common_seq.puml

   user -> pwrforge : pwrforge new my_project_1
   pwrforge -> storage : generates new project tree
   return
   return


   user -> pwrforge : pwrforge build
   alt project depends on other packages
   pwrforge -> conan : download dependencies
   conan -> pkg_repo : download dependencies
   return
   return
   end
   pwrforge -> cmake : build project
   cmake -> storage : create binary
   return
   return
   return


   user -> pwrforge : pwrforge publish
   pwrforge -> conan : conan upload
   conan -> storage : create package
   return
   conan -> pkg_repo : upload
   return
   return
   return


pwrforge and ESP-IDF
------------------

.. uml::

   !include pwrforge_common_seq.puml

   user -> pwrforge : pwrforge new --arch esp32 my_project_1
   pwrforge -> sc_new : generate src/cpp, src/cmake
   sc_new -> storage : create src/cpp, src/cmake on disk
   return
   return
   pwrforge -> sc_update : generate top level cmake
   sc_update -> storage: create top level cmake on disk
   return
   return
   return

   user -> pwrforge : pwrforge build
   pwrforge -> sc_build : execute build
   sc_build -> esp_idf : idf.py buildall (subprocess call)
   esp_idf -> storage : create binary
   return
   return
   return
   return
