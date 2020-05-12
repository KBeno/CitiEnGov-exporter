import xml.etree.ElementTree as eT
from datetime import datetime
import argparse
from urllib import request


class NameSpaceSolver:
    def __init__(self, namespace_dict):
        """
        initialize the solver instance

        :param namespace_dict: dictionary that contains the prefixes and full uris as key-value pairs
        """
        self.dict = namespace_dict

    def solve(self, full_tag):
        """
        convert element tags from prefix:tag to {full_uri}tag which is necessary for ElementTree

        :param full_tag: tag to be resolved presented as prefix:tag
        :return: resolved tag as {full_uri}tag
        """

        prefix, sep, tag = full_tag.rpartition(':')
        return '{{{uri}}}{tag}'.format(uri=self.dict[prefix], tag=tag)


class CitiEnGov:
    def __init__(self, gml_path, input_mode='file'):
        # Parse base xml with all data
        if input_mode == 'file':
            print('Opening file: {f_p}'.format(f_p=gml_path))
            gml = eT.parse(gml_path)
            self.root = gml.getroot()
        elif input_mode == 'url':
            with request.urlopen(gml_path) as url_gml:
                print('Opening URL: {u}'.format(u=gml_path))
                data = url_gml.read()
                self.root = eT.fromstring(data)
        else:
            raise ValueError('Mode should be either \'file\' or \'url\'.')

        # Prepare namespace to translate for ElementTree
        self.namespaces = {
            'CitiEnGov_01_1': 'http://maps.dedagroup.it/energy/geoserver/CitiEnGov_01_1',
            'gml': 'http://www.opengis.net/gml'
        }

        # Get all feature members
        self.feature_members = self.root.findall('./gml:featureMember', namespaces=self.namespaces)

        # get all unique UUIDs
        uuid_path = './gml:featureMember/CitiEnGov_01_1:GML_BUILDINGS_CEG/CitiEnGov_01_1:UUID'
        list_of_uuids = [uuid.text for uuid in self.root.iterfind(uuid_path, namespaces=self.namespaces)]
        self.building_UUIDs = list(set(list_of_uuids))  # get unique UUIDs

        # initiate first building object
        self.UUID_index = 0
        self.UUID = self.building_UUIDs[self.UUID_index]
        self.building = self.get_building(self.UUID)

    def get_building(self, uuid):
        feature_list = [feature for feature in self.feature_members
                        if feature.find('./CitiEnGov_01_1:GML_BUILDINGS_CEG/CitiEnGov_01_1:UUID',
                                        namespaces=self.namespaces).text == uuid]
        return Building(uuid=uuid, feature_list=feature_list, namespaces=self.namespaces)

    # make the class iterable so that it yields tha actual Building instance
    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.UUID = self.building_UUIDs[self.UUID_index]
            self.building = self.get_building(self.UUID)
            return self.building
        except IndexError:
            raise StopIteration
        finally:
            self.UUID_index += 1


class Building:
    def __init__(self, uuid, feature_list, namespaces):
        self.UUID = uuid
        self.feature_list = feature_list
        self.namespaces = namespaces

    def find(self, attribute, _all=False):
        path = './CitiEnGov_01_1:GML_BUILDINGS_CEG/CitiEnGov_01_1:{attr}'.format(attr=attribute)
        if _all:
            # return a list of xml elements containing all not None features of the building
            return [element.find(path, namespaces=self.namespaces)
                    for element in self.feature_list
                    if element.find(path, namespaces=self.namespaces) is not None]
        else:
            # return the first not None feature of the building as an xml element
            for feature in self.feature_list:
                feature_attrib = feature.find(path, namespaces=self.namespaces)
                if feature_attrib is not None:
                    return feature_attrib
            else:
                # if no feature was found for that attribute, return None:
                return None


class Inspire:
    def __init__(self):
        # Prepare the INSPIRE namespaces dictionary
        inspire_ns = {
            'xmlns': 'http://www.opengis.net/wfs',
            'wfs': 'http://www.opengis.net/wfs/2.0',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xlink': 'http://www.w3.org/1999/xlink',
            'gml':  'http://www.opengis.net/gml/3.2',
            'gmd': 'http://www.isotc211.org/2005/gmd',
            'base': 'http://inspire.ec.europa.eu/schemas/base/3.3',
            'bu-base': 'http://inspire.ec.europa.eu/schemas/bu-base/4.0',
            'bu-core2d': 'http://inspire.ec.europa.eu/schemas/bu-core2d/4.0',
        }
        self.nss = NameSpaceSolver(inspire_ns)

        # register namespaces to include it in the output file
        for prefix, uri in inspire_ns.items():
            eT.register_namespace(prefix=prefix, uri=uri)

        # Prepare INSPIRE CodeLists:
        # http://inspire.ec.europa.eu/codelist/ConditionOfConstructionValue
        self.condition_of_construction_dict = {
            'functional': 'http://inspire.ec.europa.eu/codelist/ConditionOfConstructionValue/functional',
            # TODO get list of possible values CONDITION OF CONSTRUCTION
        }

        # http://inspire.ec.europa.eu/codelist/ElevationReferenceValue
        self.elevation_reference_dict = {
            'generalroof': 'http://inspire.ec.europa.eu/codelist/ElevationReferenceValue/generalRoof'
            # TODO get list of possible values ELEVATION REFERENCE
        }

        # http://inspire.ec.europa.eu/codelist/HeightStatusValue
        self.height_status_dict = {
            'stimata': 'http://inspire.ec.europa.eu/codelist/HeightStatusValue/estimated',
            # 'measured': 'http://inspire.ec.europa.eu/codelist/HeightStatusValue/measured'
        }

        # http://inspire.ec.europa.eu/codelist/BuildingNatureValue
        self.building_nature_dict = {
            # TODO possible values from inspire codelist and citiengov codelist
        }

        # http://inspire.ec.europa.eu/codelist/CurrentUseValue
        # TODO extend list of current uses
        self.current_use_dict = {
            'ausiliario': 'http://inspire.ec.europa.eu/codelist/CurrentUseValue/ancillary',
            'negozio': 'http://inspire.ec.europa.eu/codelist/CurrentUseValue/trade',
            'residenziale': 'http://inspire.ec.europa.eu/codelist/CurrentUseValue/residential',
            'magazzino': 'http://inspire.ec.europa.eu/codelist/CurrentUseValue/trade',
            'laboratorio': 'http://inspire.ec.europa.eu/codelist/CurrentUseValue/industrial',
            'ausiliario': 'http://inspire.ec.europa.eu/codelist/CurrentUseValue/ancillary'
        }

        # http://inspire.ec.europa.eu/codelist/HorizontalGeometryReferenceValue
        self.horizontal_geometry_reference_dict = {
            # TODO horizontal geom reference values - not in use
        }

        # prepare root element attributes:
        root_attrib = {
            'xmlns': 'http://www.opengis.net/wfs',
            'numberMatched': 'unknown',
            'numberReturned': '1000',
            'timeStamp': '{ts}'.format(ts=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')),
            self.nss.solve('xsi:schemaLocation'): ('http://www.opengis.net/wfs/2.0 '
                                                   'http://schemas.opengis.net/wfs/2.0/wfs.xsd '
                                                   'http://www.opengis.net/gml/3.2 '
                                                   'http://schemas.opengis.net/gml/3.2.1/gml.xsd '
                                                   'http://inspire.ec.europa.eu/schemas/bu-core2d/4.0 '
                                                   'https://inspire.ec.europa.eu/schemas/bu-core2d/4.0/BuildingsCore2D.xsd')
        }

        # create root element
        self.root = eT.Element(self.nss.solve('wfs:FeatureCollection'))
        self.root.attrib = root_attrib

    def write_to_file(self, target_path):
        # wrap the whole data into an ElementTree object
        tree = eT.ElementTree(self.root)

        # write out the data to the target file
        print('Writing INSPIRE gml to: {path}'.format(path=target_path))
        tree.write(target_path, encoding='utf-8', xml_declaration=True, method='xml', short_empty_elements=True)

    def translate(self, citi_en_gov):

        print('Translating CitiEnGov to INSPIRE.')

        # iterate on all buildings contained in the CitiEnGov gml:
        for bu in citi_en_gov:

            # add a member to the list
            wfs_member = eT.SubElement(self.root, self.nss.solve('wfs:member'))

            # add building element
            bu_core2d_building = eT.SubElement(wfs_member, self.nss.solve('bu-core2d:Building'))

            # add elements to the building
            # LIFESPAN_BEGINNING
            begin_lifespan_version = eT.SubElement(bu_core2d_building, self.nss.solve('bu-base:beginLifespanVersion'))
            l_year = bu.find('LIFESPAN_BEGINNING').text
            begin_lifespan_version.text = '{y}-01-01T00:00:00'.format(y=l_year)

            # CONDITION_OF_CONSTRUCTION
            condition_of_construction = eT.SubElement(bu_core2d_building, self.nss.solve('bu-base:conditionOfConstruction'))
            if bu.find('CONDITION')is not None:
                cond = bu.find('CONDITION').text.lower()
                condition_of_construction.attrib = {
                    self.nss.solve('xlink:href'): self.condition_of_construction_dict[cond]}

            # DATE_OF_CONSTRUCTION
            if bu.find('DATE_C_BEGINNING') is not None:
                date_of_construction = eT.SubElement(bu_core2d_building, self.nss.solve('bu-base:dateOfConstruction'))
                date_of_event = eT.SubElement(date_of_construction, self.nss.solve('bu-base:DateOfEvent'))
                beginning = eT.SubElement(date_of_event, self.nss.solve('bu-base:beginning'))
                c_year_b = bu.find('DATE_C_BEGINNING').text
                beginning.text = '{y}-01-01T00:00:00'.format(y=c_year_b)
                if bu.find('DATE_C_END') is not None:
                    end = eT.SubElement(date_of_event, self.nss.solve('bu-base:end'))
                    c_year_e = bu.find('DATE_C_BEGINNING').text
                    end.text = '{y}-01-01T00:00:00'.format(y=c_year_e)

            # DATE_OF_RENOVATION
            if bu.find('DATE_R_BEGINNING') is not None:
                date_of_renovation = eT.SubElement(bu_core2d_building, self.nss.solve('bu-base:dateOfConstruction'))
                date_of_event_r = eT.SubElement(date_of_renovation, self.nss.solve('bu-base:DateOfEvent'))
                beginning_r = eT.SubElement(date_of_event_r, self.nss.solve('bu-base:beginning'))
                r_year_b = bu.find('DATE_R_BEGINNING').text
                beginning_r.text = '{y}-01-01T00:00:00'.format(y=r_year_b)
                if bu.find('DATE_R_END') is not None:
                    end_r = eT.SubElement(date_of_event_r, self.nss.solve('bu-base:end'))
                    r_year_e = bu.find('DATE_R_BEGINNING').text
                    end_r.text = '{y}-01-01T00:00:00'.format(y=r_year_e)

            # EXTERNAL_REFERENCE
            if bu.find('EXT_REF_REFERENCE') is not None:
                external_reference = eT.SubElement(bu_core2d_building, self.nss.solve('bu-base:externalReference'))
                external_ref = eT.SubElement(external_reference, self.nss.solve('bu-base:ExternalReference'))
                info_system = eT.SubElement(external_ref, self.nss.solve('bu-base:informationSystem'))
                info_system.text = bu.find('EXT_REF_IDENTIFIER').text
                info_system_name = eT.SubElement(external_ref, self.nss.solve('bu-base:informationSystemName'))
                loc_char_str = eT.SubElement(info_system_name, self.nss.solve('gmd:LocalisedCharacterString'))
                loc_char_str.text = bu.find('EXT_REF_INF_SYS_NAME').text
                external_ref_ref = eT.SubElement(external_ref, self.nss.solve('bu-base:reference'))
                external_ref_ref.text = bu.find('EXT_REF_REFERENCE').text

            # HEIGHT_ABOVE_GROUND
            if bu.find('HEIGHT_HEIGHT_VAL') is not None:
                height_above_ground = eT.SubElement(bu_core2d_building, self.nss.solve('bu-base:heightAboveGround'))
                height_ab_gr = eT.SubElement(height_above_ground, self.nss.solve('bu-base:HeightAboveGround'))
                height_reference = eT.SubElement(height_ab_gr, self.nss.solve('bu-base:heightReference'))
                if bu.find('HEIGHT_HEIGHT_REF') is not None:
                    height_ref = bu.find('HEIGHT_HEIGHT_REF').text.lower()
                else:
                    height_ref = 'generalroof'
                height_reference.attrib = {self.nss.solve('xlink:href'): self.elevation_reference_dict[height_ref]}
                low_reference = eT.SubElement(height_ab_gr, self.nss.solve('bu-base:lowReference'))
                height_status = eT.SubElement(height_ab_gr, self.nss.solve('bu-base:status'))
                # TODO get list of possible values HEIGHT STATUS
                height_stat = bu.find('HEIGHT_HEIGHT_STAT').text.lower()
                height_status.attrib = {self.nss.solve('xlink:href'): self.height_status_dict[height_stat]}
                height_value = eT.SubElement(height_ab_gr, self.nss.solve('bu-base:value'))
                height_value.attrib = {'uom': 'm'}
                height_value.text = bu.find('HEIGHT_HEIGHT_VAL').text

            # ID
            inspire_id = eT.SubElement(bu_core2d_building, self.nss.solve('bu-base:inspireId'))
            identifier = eT.SubElement(inspire_id, self.nss.solve('base:Identifier'))
            local_id = eT.SubElement(identifier, self.nss.solve('base:localId'))
            namespace = eT.SubElement(identifier, self.nss.solve('base:namespace'))
            local_id.text = bu.find('IDENTIFIER_ID_LOC').text
            namespace.text = bu.find('IDENTIFIER_ID_NAME').text

            # BUILDING_NATURE
            if bu.find('BUILDINGTYPE') is not None:
                building_nature = eT.SubElement(bu_core2d_building, self.nss.solve('bu-base:buildingNature'))
                building_nat = bu.find('BUILDINGTYPE').text.lower()
                building_nature.attrib = {self.nss.solve('xlink:href'): self.building_nature_dict[building_nat]}

            # CURRENT_USE
            if bu.find('USE_M') is not None:
                # divide the long string into a list of uses with percentages
                uses = bu.find('USE_M').text.split(',')
                for use in uses:
                    current_use = eT.SubElement(bu_core2d_building, self.nss.solve('bu-base:currentUse'))
                    current_us = eT.SubElement(current_use, self.nss.solve('bu-base:CurrentUse'))
                    current_u = eT.SubElement(current_us, self.nss.solve('bu-base:currentUse'))
                    percentage = eT.SubElement(current_us, self.nss.solve('bu-base:percentage'))
                    # separate use and percentage and get rid of parentheses
                    curr_use, sep, percent = use.partition('(')
                    percent = percent.strip('%)')
                    current_u.attrib = {self.nss.solve('xlink:href'): self.current_use_dict[curr_use]}
                    percentage.text = percent

            # NUMBER_OF_BUILDING_UNITS
            if bu.find('UNITS') is not None:
                number_of_building_units = eT.SubElement(bu_core2d_building,
                                                         self.nss.solve('bu-base:numberOfBuildingUnits'))
                number_of_building_units.text = bu.find('UNITS').text

            # NUMBER_OF_FLOORS_ABOVE_GROUND
            if bu.find('FLOORS') is not None:
                number_of_floors = eT.SubElement(bu_core2d_building,
                                                 self.nss.solve('bu-base:numberOfFloorsAboveGround'))
                number_of_floors.text = bu.find('FLOORS').text

            # GEOMETRY
            geometry_2d = eT.SubElement(bu_core2d_building, self.nss.solve('bu-core2d:geometry2D'))
            building_geometry_2d = eT.SubElement(geometry_2d, self.nss.solve('bu-base:BuildingGeometry2D'))
            geometry = eT.SubElement(building_geometry_2d, self.nss.solve('bu-base:geometry'))
            reference_geometry = eT.SubElement(building_geometry_2d, self.nss.solve('bu-base:referenceGeometry'))
            horizontal_geom_ref = eT.SubElement(building_geometry_2d,
                                                self.nss.solve('bu-base:horizontalGeometryReference'))
            horizontal_geom_est_acc = eT.SubElement(building_geometry_2d,
                                                    self.nss.solve('bu-base:horizontalGeometryEstimatedAccuracy'))
            polygon = eT.SubElement(geometry, self.nss.solve('gml:Polygon'))
            exterior = eT.SubElement(polygon, self.nss.solve('gml:exterior'))
            linear_ring = eT.SubElement(exterior, self.nss.solve('gml:LinearRing'))
            coordinates = eT.SubElement(linear_ring, self.nss.solve('gml:coordinates'))
            co = bu.find('GEOMETRY2D/gml:Polygon/gml:outerBoundaryIs/gml:LinearRing/gml:coordinates')
            coordinates.attrib = co.attrib
            coordinates.text = co.text

            reference_geometry.text = 'false'
            horizontal_geom_est_acc.attrib = {'uom': '!'}
            horizontal_geom_est_acc.text = '0'



class CityGML:

    def __init__(self):
        # Prepare the CityGML namespaces dictionary
        city_gml_ns = {
            # 'xmlns': 'http://www.opengis.net/wfs',
            'wfs': 'http://www.opengis.net/wfs',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xlink': 'http://www.w3.org/1999/xlink',
            'gml':  'http://www.opengis.net/gml',
            'core': 'http://www.opengis.net/citygml/2.0',
            'energy': 'http://www.sig3d.org/citygml/2.0/energy/1.0',
            'bldg': 'http://www.opengis.net/citygml/building/2.0',
        }
        self.nss = NameSpaceSolver(city_gml_ns)

        # register namespaces to include it in the output file
        for prefix, uri in city_gml_ns.items():
            eT.register_namespace(prefix=prefix, uri=uri)

        # prepare cityGML codeLists
        # https://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_usage.xml
        self.usage_dict = {
            'school': '2070',  # building for education and research
            'residential': '1000',  # residential building
            'residenziale': '1000',
            'commercio': '1150',  # business building
            'ausiliario': '2700'  # others
        }
        # https://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_roofType.xml
        self.roof_type_dict = {
            # TODO get roof types
        }

        self.height_reference_dict = {
            # TODO check values from citiengov
            'bottomOfConstruction': 'bottomOfConstruction',
            'entrancePoint': 'entrancePoint',
            'generalEave': 'generalEave',
            'generalroof': 'generalRoof',
            'generalRoofEdge': 'generalRoofEdge',
            'highestEave': 'highestEave',
            'highestPoint': 'highestPoint',
            'highestRoofEdge': 'highestRoofEdge',
            'lowestEave': 'lowestEave',
            'lowestFloorAboveGround': 'lowestFloorAboveGround',
            'lowestRoofEdge': 'lowestRoofEdge',
            'topOfConstruction': 'topOfConstruction',
            'topThermalBoundary': 'topThermalBoundary',
            'bottomThermalBoundary': 'topThermalBoundary'
        }

        # https://www.sig3d.org/codelists/citygml/2.0/energy/0.6.0/energy_BuildingType.xml
        # TODO this does not seem to be an appropriate code list...
        self.building_type_dict = {
            'ApartmentBlock': 'ApartmentBlock',
            'MultiFamilyHouse': 'MultiFamilyHouse',
            'RowHouse': 'RowHouse',
            'SingleFamilyHouse': 'SingleFamilyHouse'
        }

        # prepare root element attributes:
        root_attrib = {
            self.nss.solve('xsi:schemaLocation'): ('http://www.sig3d.org/citygml/2.0/energy/1.0 '
                                                   'http://www.citygmlwiki.org/images/a/ac/EnergyADE.xsd')
        }

        # create root element
        self.root = eT.Element(self.nss.solve('core:CityModel'))
        self.root.attrib = root_attrib

    def write_to_file(self, target_path):
        # wrap the whole data into an ElementTree object
        tree = eT.ElementTree(self.root)

        # write out the data to the target file
        print('Writing CityGML gml to: {path}'.format(path=target_path))
        tree.write(target_path, encoding='utf-8', xml_declaration=True, method='xml', short_empty_elements=True)

    def translate(self, citi_en_gov):

        print('Translating CitiEnGov to CityGML.')

        # iterate on all buildings contained in the CitiEnGov gml:
        for bu in citi_en_gov:

            # add a member to the list
            city_object_member = eT.SubElement(self.root, self.nss.solve('core:cityObjectMember'))

            # add building element
            bldg_building = eT.SubElement(city_object_member, self.nss.solve('bldg:Building'))

            # NAME
            if bu.find('NAME') is not None:
                name = eT.SubElement(bldg_building, self.nss.solve('gml:name'))
                name.text = bu.find('NAME').text

            # LIFESPAN_BEGINNING
            if bu.find('LIFESPAN_BEGINNING') is not None:
                creation_date = eT.SubElement(bldg_building, self.nss.solve('core:creationDate'))
                year = bu.find('LIFESPAN_BEGINNING').text
                creation_date.text = '{y}-01-01'.format(y=year)

            # LIFESPAN_END
            if bu.find('LIFESPAN_END') is not None:
                creation_date = eT.SubElement(bldg_building, self.nss.solve('core:terminationDate'))
                year = bu.find('LIFESPAN_END').text
                creation_date.text = '{y}-01-01'.format(y=year)

            # EXTERNAL_REFERENCE
            if bu.find('EXT_REF_REFERENCE') is not None:
                external_reference = eT.SubElement(bldg_building, self.nss.solve('core:externalReference'))
                information_system = eT.SubElement(external_reference, self.nss.solve('core:informationSystem'))
                information_system.text = bu.find('EXT_REF_IDENTIFIER').text
                external_object = eT.SubElement(external_reference, self.nss.solve('core:externalObject'))
                ext_name = eT.SubElement(external_object, self.nss.solve('core:name'))
                ext_name.text = bu.find('EXT_REF_REFERENCE').text

            # ID
            if bu.find('IDENTIFIER_ID_LOC') is not None:
                external_reference_id = eT.SubElement(bldg_building, self.nss.solve('core:externalReference'))
                information_system_id = eT.SubElement(external_reference_id, self.nss.solve('core:informationSystem'))
                information_system_id.text = bu.find('IDENTIFIER_ID_NAME').text
                external_object_id = eT.SubElement(external_reference_id, self.nss.solve('core:externalObject'))
                ext_name_id = eT.SubElement(external_object_id, self.nss.solve('core:name'))
                ext_name_id.text = bu.find('IDENTIFIER_ID_LOC').text

            # ENERGY_DEMAND
            def make_demand(energy_carrier):

                # other energy_carrier types can be added here
                if energy_carrier == 'electricity':
                    energy_source = bu.find('ENERGYAMOUNT_E_SOURCE_E').text.lower()
                    if energy_source != 'electricity':
                        raise UnboundLocalError('\'electricity\' is expected for E_SOURCE instead of {e_s}'.format(
                            e_s=energy_source))
                    energy_carrier_t = 'Electricity'
                    years = [y.text for y in bu.find('ENERGYAMOUNT_E_YEAR_ONLY_E', _all=True)]
                    uom = bu.find('CONSUMONORM_UOM_E').text.lower()  # uom is taken from the first element
                    energy_values = [v.text for v in bu.find('CONSUMONORM_VALORE_E', _all=True)]
                elif energy_carrier == 'thermal':
                    energy_source = bu.find('ENERGYAMOUNT_E_SOURCE_T').text.lower()
                    if energy_source != 'thermal':
                        raise UnboundLocalError('\'thermal\' is expected for E_SOURCE instead of {e_s}'.format(
                            e_s=energy_source))
                    years = [y.text for y in bu.find('ENERGYAMOUNT_E_YEAR_ONLY_T', _all=True)]
                    uom = bu.find('CONSUMONORM_UOM_T').text.lower()  # uom is taken from the first element
                    energy_values = [v.text for v in bu.find('CONSUMONORM_VALORE_T', _all=True)]
                    energy_carrier_t = 'HotWater'
                else:
                    raise KeyError(
                        'energy_carrier can be either \'electricity\' or \'thermal\' instead of \'{e_c}\''.format(
                        e_c=energy_carrier))
                
                demand = eT.SubElement(bldg_building, self.nss.solve('energy:demands'))
                dem = eT.SubElement(demand, self.nss.solve('energy:EnergyDemand'))
                amount = eT.SubElement(dem, self.nss.solve('energy:energyAmount'))
                time_series = eT.SubElement(amount, self.nss.solve('energy:RegularTimeSeries'))
                var_prop = eT.SubElement(time_series, self.nss.solve('energy:variableProperties'))
                time_val_prop = eT.SubElement(var_prop, self.nss.solve('energy:TimeValuesProperties'))
                aqu_method =  eT.SubElement(time_val_prop, self.nss.solve('energy:acquisitionMethod'))
                interp_type = eT.SubElement(time_val_prop, self.nss.solve('energy:interpolationType'))
                aqu_method.text = 'measurement'
                interp_type.text = 'instantaneousTotal'

                temp_ext = eT.SubElement(time_series, self.nss.solve('energy:temporalExtent'))
                time_period = eT.SubElement(temp_ext, self.nss.solve('gml:TimePeriod'))
                begin_pos = eT.SubElement(time_period, self.nss.solve('gml:beginPosition'))
                end_pos = eT.SubElement(time_period, self.nss.solve('gml:endPosition'))
                begin_pos.text = sorted(years)[0] # start year
                end_pos.text = sorted(years)[-1] # end year

                time_interval = eT.SubElement(time_series,
                                                          self.nss.solve('energy:timeInterval'))
                values = eT.SubElement(time_series, self.nss.solve('energy:values'))
                time_interval.attrib = {'unit': 'year'}
                # check if the years are consecutive:
                if len(years) != int(sorted(years)[-1]) - int(sorted(years)[0]) + 1:
                    raise UnboundLocalError('Years have to be consecutive, but here they are: {l}'.format(
                        l=sorted(years)))
                time_interval.text = str(len(years))  # number of years
                values.attrib = {'uom': uom}
                year_values = {y: v for y, v in zip(years, energy_values)}
                # list of values, separator: whitespace
                values.text = ''.join('{v} '.format(v=year_values[y]) for y in sorted(years)).strip()  # list of values

                end_use = eT.SubElement(dem, self.nss.solve('energy:endUse'))
                end_use.text = 'otherOrCombination'

                energy_carrier_type = eT.SubElement(dem, self.nss.solve('energy:energyCarrierType'))
                energy_carrier_type.attrib = {
                    'codeSpace': 'https://www.sig3d.org/codelists/citygml/2.0/energy/0.6.0/energy_EnergyCarrierType.xml'
                }
                energy_carrier_type.text = energy_carrier_t

            if not all(i is None for i in bu.find('CONSUMONORM_VALORE_E', _all=True)):
                make_demand('electricity')

            if not all(i is None for i in bu.find('CONSUMONORM_VALORE_T', _all=True)):
                make_demand('thermal')

            # USAGE
            if bu.find('USE_S') is not None:
                usage = eT.SubElement(bldg_building, self.nss.solve('bldg:usage'))
                usage.attrib = {
                    'codeSpace':'https://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_usage.xml'
                }
                predominant_use = bu.find('USE_S').text.lower()
                usage.text = self.usage_dict[predominant_use]

            # YEAR_OF_CONSTRUCTION
            if bu.find('DATE_C_BEGINNING') is not None:
                year_of_construction = eT.SubElement(bldg_building, self.nss.solve('bldg:yearOfConstruction'))
                year_of_construction.text = bu.find('DATE_C_BEGINNING').text

            # ROOF_TYPE
            if bu.find('ROOF_TYPE') is not None:
                roof_type = eT.SubElement(bldg_building, self.nss.solve('bldg:roofType'))
                roof_type.attrib = {
                    'codeSpace': 'https://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_roofType.xml'
                }
                roof_t = bu.find('ROOF_TYPE').text.lower()
                roof_type.text = self.roof_type_dict[roof_t]

            # STOREYES_ABOVE_GROUND
            if bu.find('FLOORS') is not None:
                storeys_above_ground = eT.SubElement(bldg_building, self.nss.solve('bldg:storeysAboveGround'))
                floors = bu.find('FLOORS').text
                storeys_above_ground.text = floors

                # STORY_HEIGHTS_ABOVE_GROUND
                if bu.find('H_FLOOR') is not None:
                    storey_heights = eT.SubElement(bldg_building, self.nss.solve('bldg:storeyHeightsAboveGround'))
                    storey_heights.attrib = {'uom': 'm'}
                    hei = bu.find('H_FLOOR').text
                    storey_heights.text = ''.join(['{h},'.format(h=hei) for i in range(int(floors))]).rstrip(',')

            # GEOMETRY
            lod_0_foot_print = eT.SubElement(bldg_building, self.nss.solve('bldg:lod0FootPrint'))
            multi_surface = eT.SubElement(lod_0_foot_print, self.nss.solve('gml:MultiSurface'))
            surface_member = eT.SubElement(multi_surface, self.nss.solve('gml:surfaceMember'))
            polygon = eT.SubElement(surface_member, self.nss.solve('gml:Polygon'))
            outer_boundary_is = eT.SubElement(polygon, self.nss.solve('gml:outerBoundaryIs'))
            linear_ring = eT.SubElement(outer_boundary_is, self.nss.solve('gml:LinearRing'))
            coordinates = eT.SubElement(linear_ring, self.nss.solve('gml:coordinates'))
            co = bu.find('GEOMETRY2D/gml:Polygon/gml:outerBoundaryIs/gml:LinearRing/gml:coordinates')
            coordinates.attrib = co.attrib
            coordinates.text = co.text

            # REFURBISHMENT_MEASURE
            if bu.find('DATE_R_BEGINNING') is not None:
                refurbishment_measure = eT.SubElement(bldg_building, self.nss.solve('energy:refurbishmentMeasure'))
                refurbishment_mea = eT.SubElement(refurbishment_measure, self.nss.solve('energy:RefurbishmentMeasure'))
                r_date = eT.SubElement(refurbishment_mea, self.nss.solve('energy:date'))
                r_date_of_event = eT.SubElement(r_date, self.nss.solve('energy:DateOfEvent'))
                r_period = eT.SubElement(r_date_of_event, self.nss.solve('energy:period'))
                r_time_period = eT.SubElement(r_period, self.nss.solve('gml:TimePeriod'))
                r_begin_position = eT.SubElement(r_time_period, self.nss.solve('gml:beginPosition'))
                r_end_position = eT.SubElement(r_time_period, self.nss.solve('gml:beginPosition'))
                r_level = eT.SubElement(refurbishment_mea, self.nss.solve('energy:level'))
                r_begin_position.text = bu.find('DATE_R_BEGINNING').text
                r_end_position.text = bu.find('DATE_R_END').text
                r_level.text = 'unknown'

            # ENERGY_PERFORMANCE_CERTIFICATION
            if bu.find('ENERGYPERFORMANCE_PERF_CLASS') is not None:
                energy_certification = eT.SubElement(bldg_building,
                                                     self.nss.solve('energy:energyPerformanceCertification'))
                energy_cert = eT.SubElement(energy_certification,
                                            self.nss.solve('energy:EnergyPerformanceCertification'))
                cert_rating = eT.SubElement(energy_cert, self.nss.solve('energy:rating'))
                cert_name = eT.SubElement(energy_cert, self.nss.solve('energy:name'))
                cert_id = eT.SubElement(energy_cert, self.nss.solve('energy:certificationId'))
                cert_rating.text = bu.find('ENERGYPERFORMANCE_PERF_CLASS').text
                cert_name.text = bu.find('ENERGYPERFORMANCE_PERF_METHOD').text
                # TODO cert id is missing

            # HEIGHT_ABOVE_GROUND
            if bu.find('HEIGHT_HEIGHT_VAL') is not None:
                height_above_ground = eT.SubElement(bldg_building, self.nss.solve('energy:heightAboveGround'))
                height_above_gr = eT.SubElement(height_above_ground, self.nss.solve('energy:HeightAboveGround'))
                height_reference = eT.SubElement(height_above_gr, self.nss.solve('energy:heightReference'))
                height_value = eT.SubElement(height_above_gr, self.nss.solve('energy:value'))
                h_reference = bu.find('HEIGHT_HEIGHT_REF').text.lower()
                height_reference.text = self.height_reference_dict[h_reference]
                height_value.attrib = {'uom': 'm'}
                height_value.text = bu.find('HEIGHT_HEIGHT_VAL').text

            # VOLUME
            if bu.find('VOLUME_VALUE') is not None:
                gross_volume = eT.SubElement(bldg_building, self.nss.solve('energy:volume'))
                gross_volume_type = eT.SubElement(gross_volume, self.nss.solve('energy:VolumeType'))
                gross_volume_typ = eT.SubElement(gross_volume_type, self.nss.solve('energy:type'))
                gross_volume_value = eT.SubElement(gross_volume_type, self.nss.solve('energy:value'))
                gross_volume_typ.text = 'grossVolume'
                gross_volume_value.attrib = {'uom': 'm3'}
                gross_volume_value.text = bu.find('VOLUME_VALUE').text

            if bu.find('ENERGYPERF_VOLUME_VALUE') is not None:
                energy_volume = eT.SubElement(bldg_building, self.nss.solve('energy:volume'))
                energy_volume_type = eT.SubElement(energy_volume, self.nss.solve('energy:VolumeType'))
                energy_volume_typ = eT.SubElement(energy_volume_type, self.nss.solve('energy:type'))
                energy_volume_value = eT.SubElement(energy_volume_type, self.nss.solve('energy:value'))
                energy_volume_typ.text = 'energyReferenceVolume'
                energy_volume_value.attrib = {'uom': 'm3'}
                energy_volume_value.text = bu.find('ENERGYPERF_VOLUME_VALUE').text

            # FLOOR_AREA
            if bu.find('SURFACE_VALUE') is not None:
                floor_area = eT.SubElement(bldg_building, self.nss.solve('energy:floorArea'))
                floor_ar = eT.SubElement(floor_area, self.nss.solve('energy:FloorArea'))
                floor_area_type = eT.SubElement(floor_ar, self.nss.solve('energy:type'))
                floor_area_value = eT.SubElement(floor_ar, self.nss.solve('energy:value'))
                floor_area_type.text = 'grossFloorArea'
                floor_area_value.attrib = {'uom': 'm2'}
                floor_area_value.text = bu.find('SURFACE_VALUE').text

            # OCCUPANTS

            # BUILDING_TYPE
            if bu.find('BUILDINGTYPE') is not None:
                building_type = eT.SubElement(bldg_building, self.nss.solve('energy:buildingType'))
                building_type.attrib = {
                    'codeSpace': 'https://www.sig3d.org/codelists/citygml/2.0/energy/0.6.0/energy_BuildingType.xml'
                }
                building_typ = bu.find('BUILDINGTYPE').text.lower()
                building_type.text = self.building_type_dict[building_typ]


if __name__ == '__main__':

    # parse command line arguments
    parser = argparse.ArgumentParser(description='Translate input CitiEnGov GML to a standard compliant GML')
    origin = parser.add_mutually_exclusive_group()
    origin.add_argument('-u', '--url', help='set input mode to url', action='store_true')
    origin.add_argument('-f', '--file', help='set input mode to file', action='store_true')
    parser.add_argument('input', help='path to the input CitiEnGov gml to be translated', type=str)
    parser.add_argument('output', help='path where the output gml can be written', type=str)
    parser.add_argument('standard', help='the standard to make the output compliant to', type=str,
                        choices=['INSPIRE', 'CityGML'])
    args = parser.parse_args()

    # prepare (read) CitiEnGov gml
    if args.url:
        mode = 'url'
    elif args.file:
        mode = 'file'
    else:
        raise ValueError('Input mode can be either \'url\' or \'file\'!')
    CitiEG = CitiEnGov(gml_path=args.input, input_mode=mode)

    # prepare standard to use
    if args.standard == 'INSPIRE':
        standard = Inspire()
    elif args.standard == 'CityGML':
        standard = CityGML()
    else:
        raise ValueError('Standard can be either \'INSPIRE\' or \'CityGML\'!')

    # do the translation
    standard.translate(citi_en_gov=CitiEG)

    # write result out to file
    standard.write_to_file(args.output)
