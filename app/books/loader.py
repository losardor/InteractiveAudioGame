from app.books.view import waypoint
from app.models.option import Option
from app.models.waypoint import Waypoint
from json import load as jload
from app.models import Book, Waypoint,TextContent
from app import db


class BookLoader():

    def __init__(self,book_dict):
        self.book_dict = book_dict
        self.book = None
        self.wps = {}
        self.options = {}
        self.wp_mapping = dict()

    def validate():
        pass

    def load(self):
        self._create_book(**self.book_dict)
        self._create_wps(**self.book_dict)
        self._create_options(**self.book_dict)
        self._create_content(**self.book_dict)

        db.session.commit()


    def _create_book(self,name,description,**book_dict_kwargs):
        self.book = Book(name=name,description=description,owner_id=1)
        db.session.add(self.book)
        db.session.flush()

    def _create_wps(self,waypoints,**book_dict_kwargs):
        for wp in waypoints:
            new_wp = Waypoint(book_id=self.book.id,start=wp.get("start",False))
            db.session.add(new_wp)
            db.session.flush()
            self.wp_mapping[wp["id"]] = new_wp.id


            

    def _create_options(self,waypoints,**bool_dict_kwargs):
        for wp in waypoints:
            for opt in wp["options"]:
                option_dict= {"sourceWaypoint_id":self.wp_mapping[wp["id"]],
                        "destinationWaypoint_id":self.wp_mapping[opt["destinationWaypoint_id"]],
                        "linkText":opt["linkText"]}
                opt = Option(**option_dict)
                db.session.add(opt)
                db.session.flush()

    def _create_content(self,waypoints,**bool_dict_kwargs):
         for wp in waypoints:
             if wp["content"]["type"] == "text":
                cnt = TextContent(content=wp["content"]["data"],
                waypoint_id =self.wp_mapping[wp["id"]])
             else:
                cnt = TextContent(content=None,
                waypoint_id =self.wp_mapping[wp["id"]])
             db.session.add(cnt)
             db.session.flush()




class JsonFileBookLoader(BookLoader):

    def __init__(self,file_name):
        with open(file_name,"r") as json_file:
            book_dict = jload(json_file)

        super().__init__(book_dict)

    