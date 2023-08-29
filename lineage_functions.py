import requests
from xml.etree import ElementTree
from datetime import datetime

def get_feature_history_url(featureid,type='way'):
    return f'https://www.openstreetmap.org/api/0.6/{type}/{featureid}/history'

def parse_datetime_str(inputstr,format='ymdhms'):

    format_dict = {
        'ymdhms' : "%Y-%m-%dT%H:%M:%SZ",
    }

    return datetime.strptime(inputstr,format_dict[format])


def get_datetime_update_info(featureid,featuretype='way',onlylast=True,return_parsed=True,return_special_tuple=True,desired_index=-1):

    h_url = get_feature_history_url(featureid,featuretype)

    try:
        response = requests.get(h_url)
    except:
        if onlylast:
            if return_parsed and return_special_tuple:
                return [None]*4 #4 Nones

            return ''
        else:
            return []

    if response.status_code == 200:
        tree = ElementTree.fromstring(response.content)

        element_list = tree.findall(featuretype)

        if element_list:
            # date_rec = [element.attrib['timestamp'][:desired_index] for element in element_list]
            date_rec = [element.attrib['timestamp'] for element in element_list]
            print(date_rec)

            if onlylast:
                if return_parsed:
                    if return_special_tuple:
                        # parsed = datetime.strptime(date_rec[desired_index],'%Y-%m-%dT%H:%M:%S')
                        parsed = parse_datetime_str(date_rec[desired_index])
                        return len(date_rec),parsed.day,parsed.month,parsed.year

                    else:
                        # return datetime.strptime(date_rec[desired_index],'%Y-%m-%dT%H:%M:%S')
                        return parse_datetime_str(date_rec[desired_index])

                
                else:
                    return date_rec[desired_index]

            else:
                if return_parsed:
                    return [parse_datetime_str(record) for record in date_rec]

                else:
                    return date_rec


        else:
            if onlylast:
                return ''
            else:
                return []
    
    else:
        print('bad request, check feature id/type')
        if onlylast:
            return ''
        else:
            return []

