# FIXME: before you push into master...
RUNTIMEDIR=D:/openmodelica/include/omc/c/
#COPY_RUNTIMEFILES=$(FMI_ME_OBJS:%= && (OMCFILE=% && cp $(RUNTIMEDIR)/$$OMCFILE.c $$OMCFILE.c))

fmu:
	rm -f 933.fmutmp/sources/LongitudinalVehicle_init.xml
	cp -a "D:/openmodelica/share/omc/runtime/c/fmi/buildproject/"* 933.fmutmp/sources
	cp -a LongitudinalVehicle_FMU.libs 933.fmutmp/sources/

