#!/usr/bin/env python3
# --- shebangline ---

#
# @Martin Juricek
#

import copy
import json
import sys

import dash

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go

from dash.dependencies import Input, Output

from geopy.geocoders import Nominatim
from geopy import distance

class Nodes_Airports(object):
    def __init__(self, name_city):
        self.city = name_city
        self.locator(self.city)

    def locator(self, name_city):
        # nastaveni geolocatoru z knihovny geopy
        geolocator = Nominatim(user_agent="VZI_project")
        val = False
        
        # provedeni lokace zadaneho mesta
        location = geolocator.geocode(name_city, addressdetails=True, language='en')
        
        # zjisteni zdali je zadany rozumny retezec pro lokaci a jestli bylo nalezeno vubec mesto se vstupnim retezcem
        if location is None:
            raise ValueError("Put right name of City!")

        for i in location.raw['address']:
            if i == 'city':
                val = True
                break

        if not val:
            raise ValueError("Put right name of City!")
        
        # prirazeni mesta, stat
        new_node, county = location.raw['address']['city'], location.raw['address']['country']
        print('Do u have on mind: ' + location.raw['address']['city'] + ', ' + location.raw['address']['country'] + '?')
        
        con = input("Enter your value [y/n]: ") 
        if con == 'y' or con == 'Y':
            print(new_node + '-' + county + ' [' + 'latitude: ' + str(location.latitude) + ', longitude: ' + str(location.longitude) + ']')
            
            old_node = input("Add to node city: ")

            #volani funkce k validaci a prohledani souboru s daty
            latitude_, longitude_ = self.validation(new_node, old_node)

            # ulozeni souradnic, kdy new_node_loc = nove mesto(uzel), old_node_loc = jiz zaznamenany mesto(uzel) 
            new_node_loc = [location.latitude, location.longitude]
            old_node_loc = [latitude_, longitude_]

            # kalkulace casu jako parametr pro hranu grafu
            time = self.calculator(new_node_loc, old_node_loc)

            # pridani uzlu a hran do databaze
            self.add_node(new_node, old_node, new_node_loc, time)

        else:
            print("Exit!!")

    def add_node(self, add_city, city, add_city_loc, time):
        # uzly jsou ve strukture reprezentovany jako city-Airport
        add_city = add_city + '-Airport'
        
        # vytvoreni slovniku slozici k zapisu do externich souboru
        data={add_city:{'lat': str(add_city_loc[0]), 'lon': str(add_city_loc[1]) }}
        data2 = {add_city:{city:time},}

        # zapis a updatuj jiz existujicih data v externich souborech
        with open('airports_location.json', 'r+') as infile:
            locations = json.load(infile)

            infile.seek(0) 

            locations.update(data)
            json.dump(locations, infile, indent=2)

            infile.truncate()      
        infile.close()
        
        with open('flights_data.json', 'r+') as outfile:
            f_data = json.load(outfile)
            outfile.seek(0)
            
            # pokud je jiz existujici mesto v databazi jen updatuj
            if add_city in f_data.keys():
                f_data[add_city].update({city: time})
                f_data[city].update({add_city: time})

            # vytvor zcela novy uzel a zapis relevantni uzel s delkou hrany, updatuj uzel
            else:
                f_data[city].update({add_city: time})
                f_data.update(data2)

            json.dump(f_data,outfile, indent=2)

            outfile.truncate()   
        outfile.close()

    def calculator(self, node_1, node_2):
        # vzdalenost od dvou uzlu zaokrouhlena a v jednotkach km, podelena konstantou velocity, ktera reprezentuje prumernou rychlost letadla,
        # funkce nasledne vraci cas jako parametr hrany

        velocity = 515
        distance_airline = round(distance.distance(node_1, node_2).kilometers,0)
        time = int(round((distance_airline/velocity)*60,0))
        return time

    def validation(self, add_city, search_city):
        # ve funkci je provadena validace zda-li vstupni hodnoty odpovidaji hodnotam v databazi a pripadne jsou vraceny souradnice
        # funkce i resi jestli byl zadan spravny vstup ktery by odpovidal datum v externich souborech
        # take resi validaci jestli existuje jiz zadana trasa 
        
        add_city = add_city+"-Airport"
                
        with open('flights_data.json', 'r') as outfile:
            distances = json.load(outfile)
        
        if not search_city in distances.keys():
            raise ValueError ("Put in form: 'city-Airport'")
        
        for i in distances[search_city].keys():
            if i == add_city:
                latitude = None
                longitude = None
                print("Sorry but this flight record already exists!!")
                break

        with open('airports_location.json', 'r') as outfile:
            locations = json.load(outfile)
        
        for i in locations.keys():
            if i == search_city:        
                latitude = locations[i]['lat']
                longitude = locations[i]['lon']
                
        return latitude, longitude
        
class Run_App(object):
    def load_city_data(self):
        # nacitani dat ulozenych v externich souborech databaze popisujici strukturu grafu 
        
        with open('flights_data.json', 'r') as outfile:
            distances = json.load(outfile)       

        return distances
    
    def load_city_name(self):
        # nacitani dat o jednotlivych mestech, slouzici k vykresleni

        with open('airports_location.json', 'r') as outfile:
            locations = json.load(outfile)

        city = []

        # prohledej v datech
        for i in locations:   
            city.append(i)
              
        return city
    
    def load_city_location(self, airports):
        # nacitani dat o jednotlivych mestech, slouzici k vykresleni
        # pri nalezeni pozadovaneho mesta jsou vraceny jeho souradnice

        with open('airports_location.json', 'r') as outfile:
            locations = json.load(outfile)

        latitude,longitude = [], []

        # prohledej v datech
        for k in airports:
            for i in locations.keys():
                if i == k:
                    latitude.append(locations[i]['lat'])
                    longitude.append(locations[i]['lon'])
                    break

        return latitude, longitude
    # inicializacni graf, vykresli vsechny zname uzly
    def show(self):

        city_ = self.load_city_name()
        lat_, lon_ = self.load_city_location(city_)
        
        fig = go.Figure()
        fig.add_trace(go.Scattergeo(

            lat = lat_[:],
            lon = lon_[:],
            
            text = city_[:],
            mode = 'markers',

            marker = dict(size = 12, color = 'darkred'),
            ),        
        )
        
        fig.update_layout(
            width=1835,
            height=930,
            # autosize = True
            showlegend = False,
            geo = dict(
                showland = True,
                showlakes = True,
                showcountries = True,
                showocean = True,
                showrivers=True, 
                rivercolor = 'rgb(0, 92, 149)',
                oceancolor = 'rgb(0, 159, 228)',          
                landcolor = 'rgb(196, 206, 86)',
                showsubunits = True,
                countrycolor = 'rgb(0, 0, 0)',
                #resolution 50
                resolution = 110,
                lakecolor = 'rgb(0, 92, 149)',

                projection_type = 'orthographic',
                coastlinewidth = 2,
            )
        )
        return fig
    # geo graf, ktery vykresli nejkratsi cestu, vylepsen o animaci
    def show_path(self, path):
        # count
        c = len(path)

        # nacteni souradnic pro vykresleni
        lat_, lon_ = self.load_city_location(path)

        # zobrazeni grafu jako zemekouli spolu s moznosti animace, dale jsou definovany uzly jako
        # cervene tecky, a hrany jako cervene cary 
        fig = go.Figure(
            data=go.Scattergeo(

            lat = lat_[:],
            lon = lon_[:],
            
            text = path,
            mode = 'lines+markers',

            marker = dict(size = 12, color = 'black'),
            line = dict(width = 5, color = 'black'),
        ),

        # definovani snimku k animaci
        frames=[
            go.Frame(data=[
                go.Scattergeo(
                    lat = lat_[:+k+1],
                    lon=lon_[:+k+1])
                    ])
                for k in range(c)
            ]    
        )

        # update vizualniho rozhrani, jako je text, anim. button, barvy, hrany a rozliseni
        # pri nastaveni rozliseni na 50 se zvysi presnost 
        fig.update_layout(
            title={
                'text': "HIT BUTTON!!",
                'xanchor': 'left',
                'yanchor': 'top'},

            title_font_color="purple",

            showlegend = False,
            updatemenus=[
                dict(
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.085,
                    xanchor="left",
                    y=1.095,
                    yanchor="top",
                    type="buttons",
                          buttons=[
                            dict(label="ANIMATION",
                                        method="animate",
                                        args=[None])])],
            geo = dict(
                showland = True,
                showlakes = True,
                showcountries = True,
                showocean = True,
                showrivers=True, 
                rivercolor = 'rgb(0, 92, 149)',
                oceancolor = 'rgb(0, 159, 228)',          
                landcolor = 'rgb(196, 206, 86)',
                showsubunits = True,
                countrycolor = 'rgb(0, 0, 0)',
                #resolution 50
                resolution = 110,
                lakecolor = 'rgb(0, 92, 149)',

                projection_type = 'orthographic',
                coastlinewidth = 2,
            )
       
        )
        return fig
        
    def show_app(self):
        # zavolej funkci k zobrazeni inicializacniho grafu
        figure = self.show()
        # pouzil jsem vychozi externi style z nabidky ploly dashboard
        external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
        
        app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

        # vytvoreni layotu s appky se zobrazeni geo grafu
        app.layout = html.Div([
            dcc.Graph(
                id='basic-interactions',
                figure=figure
            ),  
        ])
        # nastav promenou do ktere budou ulozene zakliknute data
        pom = []

        # dashboard app callback
        @app.callback(
        # vystup bude meneni geo grafu, vstup jsou data zakliknuta ze zobrazeneho geo grafu
        Output('basic-interactions', 'figure'),
        [Input('basic-interactions', 'clickData')])
        def display_click_data(clickData):
            # Je nutne resit inicializacni zakliknuti a spravne vraceni parametru 
            if clickData != None:
                # ulozeni dat z geo grafu do promene
                pom.append(clickData['points'][0]['text'])

                # pokud je zakliknuty bod, pridej stopu do grafu, tedy je pridan cerny bod do puvodniho grafu
                if len(pom) == 1:
                    figure_2 = self.show()

                    airport = [pom[0]]
                    lat_, lon_ = self.load_city_location(airport)

                    figure_2.add_trace(
                        go.Scattergeo(

                        lat = lat_,
                        lon = lon_,
                        
                        text = pom[0],
                        mode = 'markers',

                        marker = dict(size = 20, color = 'black'),
                        )
                    )
                    
                    return figure_2

                if len(pom) == 2:  
                    # pokud jsou zakliknute 2 body nasledne proved vypocet Dijkstrova algoritmu a zobraz vysledek
                    dijktra = Dijkstra(pom[0], pom[1],self.load_city_data())
                    figure_show = self.show_path(dijktra.path)
                    
                    return figure_show
                
                if len(pom) > 2:
                    # pokud je zakliknut 3 bod, vynuluj pole promene a vrat inicializacni geograf
                    for i in range(3):
                        del pom[0]

                    return figure

            else:
                print(" ** If u want add node city press 'ctr+c' !! ** ")
                return figure
        # Python Flask run server 
        app.run_server(debug=True)
    
class Dijkstra(object):
    def __init__(self, start, end, dist):
        # promena ktera je nasledne volana do tridy k vykreslovani geo grafu
        self.path = []
        
        self.city_eval= {}
        self.dist_eval= {}
        self.visited = []

        self.start = start
        self.end = end
        self.dist = dist

        self.null(self.dist)
        self.dijkstra(start, end, self.dist)

    def null(self, dist):
        # pro vsechny vrcholy je ohodnoceni hran(dist_eval) = +infinity, a stavu(city_eval) = nedefinovan       
        dist_eval = self.dist_eval
        city_eval = self.city_eval

        for i in dist.keys():
            dist_eval[i] = float('Inf')
            city_eval[i] = None

    def take_node(self, dist_eval, visited):
        # vyber otevreny vrchol, jehož delka hrany je nejmensi
        
        # deep copy vs shallow copy 
        dist_eval_t = copy.deepcopy(dist_eval)

        for node in visited:
            del dist_eval_t[node]

        return min(dist_eval_t, key = lambda k: dist_eval_t[k])
        
    def shortest_path(self, start_node, end_node, records):
        shortest_path = [end_node]

        # k vysledne nejkratsi ceste pridavej uzly z vzpoctu, dokud se nebude rovnat koncovy uzel sve prave hodnote tim padem pocatecnimu uzlu
        while True:
            shortest_path.append(records.get(end_node))
            end_node = records.get(end_node)

            if end_node == start_node:
                break

        for i in range(len(shortest_path),0,-1):
            if i == 1:
                pass
            else:
                print(shortest_path[i-1] + " -> " + shortest_path[i-2])
        
        # vrat funkci v obracenem poradi
        return shortest_path[::-1]
    
    def dijkstra(self, start, end, dist):
        dist_eval = self.dist_eval
        city_eval = self.city_eval
        visited = self.visited

        # pro prvni zapoceti vypoctu urci hranu(dist_eval) = 0, a stav(city_eval) = startovni mesto   
        dist_eval[start] = 0
        city_eval[start] = start

        # pokud se startovni uzel rovna koncovemu vypocet je ukonce
        if start == end:
            print('You stand in one place!')

        # dokud existuji nejake otevrene vrcholy provadej:
        while True:   
            # urcuje nam nejkratsi uzle 
            node = self.take_node(dist_eval, visited)

            # pro vsechny nasledovniky w z vrcholu v
            for i in dist[node].keys():
                if i in visited:
                    continue
                
                # tedy pokud je hrana nasledovnika vetsi jak hrana sveho predchudcu mezi vrocholy (w,v) uloz danou hranu
                if dist_eval[i] > dist_eval[node] + dist[node].get(i):
                    dist_eval[i] = dist_eval[node] + dist[node].get(i)
                    city_eval[i] = node
            
            # urceni navstivenych uzlu
            visited.append(node)

            if end in visited:
                break
        
        self.path = self.shortest_path(start, end, city_eval)

        print('It takes about {} min'.format(dist_eval.get(end)))

def main():
    app = Run_App()
    app.show_app()

    print("\n\n You have shut down the server!! \n")
    print("For end put 'exit' or add node! \n")
    
    try:
        num = input("Choose city: ")
    except:
        raise KeyError("Wrong key interrupt!") 
    
    if num == 'exit':
        sys.exit()
    else:
        geoloc = Nodes_Airports(num)
    
if __name__ == "__main__":
    main()