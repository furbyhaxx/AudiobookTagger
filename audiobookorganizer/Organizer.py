import os
import sys

import music_tag

from pathlib import Path

from audiobookorganizer.core.Helpers import MetadataDict
from audiobookorganizer.core.Tagger import FileMetadata
from audiobookorganizer.core.Utils import has_subfolders, get_filetype, get_folders_from_path, get_first_audio_file
from audiobookorganizer.metadata.GoogleBooks import Provider as GoogleBooksProvider
import cli_ui as ui


class App:
    _VERSION = "0.0.1 alpha"

    _MENU_ITEM_CHECK_TAGS = "Check for missing Tags"
    _MENU_ITEM_ORGANIZE = "Organize Audiobooks ins Folders"
    _MENU_ITEM_EXIT = "Exit"

    def __init__(self, source="", destination=None):
        self.metadataprovider = GoogleBooksProvider()
        pass

    def main_menu(self):
        tasks = [
            # App._MENU_ITEM_CHECK_TAGS,
            App._MENU_ITEM_ORGANIZE,
            App._MENU_ITEM_EXIT
        ]
        choice = ui.ask_choice("Choose a task [" + App._MENU_ITEM_ORGANIZE + "]", choices=tasks)

        if choice is None:
            # ui.error("Please select a task")
            # self.main_menu()
            choice = App._MENU_ITEM_ORGANIZE

        if choice == App._MENU_ITEM_CHECK_TAGS:
            self.check_tags()
        elif choice == App._MENU_ITEM_ORGANIZE:
            self.organize()
        elif choice == App._MENU_ITEM_EXIT:
            print(choice)

    def check_tags(self):
        path = ui.ask_string("Enter path to your audiobooks")
        if path is None:
            path = "\\\\10.1.1.210\\media\\audio\\audio_books"
            path = "C:\\Users\\Vital\\OpenAudible\\books"
        ui.info("Checking tags in", ui.bold, path)

        for root, d_names, f_names in os.walk(path):
            if not has_subfolders(root):

                folder = root.replace(path + "\\", "")
                folders = get_folders_from_path(folder)

                path_author, path_series, path_title = None, None, None

                if len(folders) == 2:  # author, title
                    path_author = folders[0]
                    path_title = folders[1]
                elif len(folders) == 3:  # author, series, title
                    path_author = folders[0]
                    path_series = folders[1]
                    path_title = folders[2]
                elif len(folders) == 1:  # should be title fo book
                    path_title = folders[0]
                    ui.info("Only detected book title from path", ui.bold, path_title)
                else:
                    ui.error("Folder structure of", folder, "not ok skipping")
                    ui.info("TODO: implement user handling")
                    # TODO: implement user handling of corrupted folder structure
                    continue

                ui.info(ui.green, "Found Book:", ui.reset, ui.bold, "Title:", ui.reset, path_title, ui.reset, ui.bold,
                        "Author:", path_author, ui.reset, ui.bold, "Series:", path_series, ui.reset)

                file = get_first_audio_file(root, f_names)
                metadata = FileMetadata(os.path.join(root, file))

                # ui.info(ui.green, "Metadata (Path/File):", ui.reset,
                #         ui.bold, "Title:", ui.reset, path_title, "/", metadata.get("title"),
                #         ui.bold, "Author:", ui.reset, path_author, "/", metadata.get("author"),
                #         ui.bold, "Series:", ui.reset, path_series, "/", metadata.get("series"),
                #         )

                results = self.metadataprovider.search(author=metadata.get("author"), title=metadata.get("title"), getfirst=True)

                if len(results) > 0:
                    pass

                headers = ["Tag", "File", "New"]
                data = []
                for key, value in FileMetadata.TAGMAP.items():
                    fval = str(metadata.get(key))
                    fval = None if str(fval) == "" else fval

                    # new_color = ui.green if fval != str(results.get(key)) else ui.red if results.get(
                    #     key) is None else ui.reset,

                    # fval = str(fval)[:40] + '..' if len(str(fval)) > 40 else fval

                    new = results.get(key)

                    data.append((
                        (ui.bold, key),
                        (
                            ui.red if fval is None else ui.reset,
                            str(fval)[:40] + '..' if len(str(fval)) > 40 else fval
                        ),
                        (
                            # ui.green if fval != str(results.get(key)) else ui.red if results.get(key) is None else ui.reset,
                            ui.red if results.get(key) is None else ui.green if fval != str(results.get(key)) else ui.reset,

                            # ui.red if results.get(key) is None else ui.green,
                            str(results.get(key))[:40] + '..' if len(str(results.get(key))) > 40 else results.get(key)
                        )))

                # data = [
                #     [(ui.bold, "John"), (green, 10.0), None],
                #     [(bold, "Jane"), (green, 5.0)],
                # ]

                ui.info_table(data, headers=headers)

                for item in FileMetadata.UPDATABLE_TAGS:
                    metadata.update(item, results.get(item))

                metadict = metadata.new_metadata

                for file in f_names:
                    # print(root, file)
                    # print(filetype(file))
                    if get_filetype(os.path.join(root, file))[0] == "audio":
                        metaobj = FileMetadata(os.path.join(root, file))
                        metaobj.new_metadata = metadict
                        metaobj.save()
                # tagread(os.path.join(root))
                # print(root, d_names, f_names)

    # def _update_metatags(self):
    #     file = get_first_audio_file(root, f_names)
    #     file = music_tag.load_file(file)
    #     metadata = FileMetadata(os.path.join(root, file))

    def _show_changes_table(self, meta_orig, meta_new):
        headers = ["Tag", "File", "New"]
        data = []

        for key in FileMetadata.UPDATABLE_TAGS:
            if meta_new.has_changed():  # has metadata changed at all?
                if meta_orig[key] != meta_new[key]:  # is this tag different than before? (Maybe keep track of changed tags inside MetadataDict)
                    data.append((
                        (
                            ui.bold,    # color col1
                            key         # value col1
                        ),  # col1
                        (
                            ui.reset,  # color col2
                            str(meta_orig[key])[:40] + '..' if len(str(meta_orig[key])) > 40 else meta_orig[key]  # value col2

                        ),  # col2
                        (
                            ui.green,  # color col2
                            (str(meta_new[key])[:40] + '..' if len(str(meta_new[key])) > 40 else meta_new[key]) if not isinstance(meta_new[key], list) else list(set(meta_new[key]))   # value col2
                        ),  # col3
                    ))
                else:  # is this tag different than before? (Maybe keep track of changed tags inside MetadataDict)
                    data.append((
                        (
                            ui.bold,    # color col1
                            key         # value col1
                        ),  # col1
                        (
                            ui.reset,  # color col2
                            str(meta_orig[key])[:40] + '..' if len(str(meta_orig[key])) > 40 else meta_orig[key]  # value col2

                        ),  # col2
                        (
                            ui.reset,  # color col2
                            ""  # value col2
                        ),  # col3
                    ))

        if len(data) > 0:
            ui.info_table(data, headers=headers)
        else:
            ui.info("Book:", meta_orig.Title, "from", meta_orig.Author, "has not changed")

    def _make_path_segment_compatible(self, path, deletechars='\/:*?"<>|'):

        for c in deletechars:
            path = path.replace(c, '')
        return path

    def _walk_path(self, path, output=None, dryrun=True, confirm_action=True, writetags=True, createfolders=True, move=True):
        for root, d_names, f_names in os.walk(path):
            if not has_subfolders(root):  # no more subfolders, here should be audio files
                if root == path:
                    # no folders, just files
                    for file in f_names:
                        if get_filetype(os.path.join(root, file))[0] == "audio":
                            filemeta = MetadataDict.from_file(os.path.join(root, file))
                            audiblemeta = MetadataDict.from_audible(filemeta.Author, filemeta.Title)
                            gbmeta = MetadataDict.from_googlebooks(filemeta.Author, filemeta.Title)
                            # print(filemeta)
                            # print(gbmeta)

                            meta_new = filemeta.copy()
                            meta_new.update(gbmeta)
                            meta_new.forceupdate(audiblemeta)  # force audible metadata


                            ui.info("Book:", filemeta.Title, "from", filemeta.Author)

                            self._show_changes_table(filemeta, meta_new)


                            # filemeta.update(gbmeta)
                            # print(filemeta)

                            if not meta_new.has_changed():
                                if ui.ask_yes_no("No metadata found, should I skip this book for now?", default=True):
                                    continue






                            if confirm_action:
                                choice = ui.ask_yes_no("Should I do that?", default=True)
                                if choice:
                                    del filemeta
                                    filemeta = meta_new
                                else:
                                    continue


                            # print(f'filemeta has changed? { filemeta.has_changed()}')
                            if not dryrun:
                                filemeta.save_to_file()

                            self._generate_folder_structure(root, file, filemeta, output=output, dryrun=dryrun)

                else:  # folder structure
                    folders = self._get_folders_from_path(root, path)

                    if len(folders) == 1:  # only book name
                        title = folders[0]
                        author = None
                        series = None
                    elif len(folders) == 2:  # author and books name
                        author = folders[0]
                        title = folders[1]
                        series = None
                    elif len(folders) == 3:  # author, series, bookname
                        author = folders[0]
                        series = folders[1]
                        title = folders[2]

                    for file in f_names:
                        if get_filetype(os.path.join(root, file))[0] == "audio":

                            meta = MetadataDict({
                                "Author": author,
                                "Title": title,
                                "Series": series
                            })

                            meta = MetadataDict.from_file(os.path.join(root, file), defaults=meta)
                            audiblemeta = MetadataDict.from_audible(meta.Author, meta.Title)
                            gbmeta = MetadataDict.from_googlebooks(meta.Author, meta.Title)

                            meta_new = meta.copy()
                            meta_new.update(gbmeta)
                            meta_new.forceupdate(audiblemeta)  # force audible metadata

                            ui.info("Book:", ui.bold, meta.Title, ui.reset, "from", ui.bold, meta.Author)

                            self._show_changes_table(meta, meta_new)

                            if writetags:
                                if not dryrun:
                                    if confirm_action:
                                        yn = ui.ask_yes_no("Should I save those tags to file?", default=True)
                                        if yn:
                                            meta_new.save_to_file(meta["file"].filename)
                                    else:
                                        ui.info("writing tags to file")
                                        meta_new.save_to_file()
                                else:
                                    ui.warning(ui.bold, "[DRYRUN]", ui.reset, "Writing tags")

                            self._generate_folder_structure(root, file, meta_new,
                                                            output=output,
                                                            dryrun=dryrun,
                                                            createfolders=createfolders,
                                                            move=move,
                                                            confirm_action=confirm_action
                                                            )

                            # if createfolders:
                            #     if not dryrun:
                            #         if confirm_action:
                            #             yn = ui.ask_yes_no("Should I create the folder structure?", default=True)
                            #     else:
                            #         ui.warning(ui.bold, "[DRYRUN]", ui.reset, "Creating folderstructure")

                            # print("test")


    def _generate_folder_structure(self, path, file, metadata, output=None, save_cover=True, move=True, dryrun=True, confirm_action=False, createfolders=True):  # if move=False, file will be copied

        if metadata.Series is None:
            fullpath = os.path.join(path if output is None else output,
                                    self._make_path_segment_compatible(metadata.Author),
                                    self._make_path_segment_compatible(metadata.Title))
        else:
            fullpath = os.path.join(path if output is None else output,
                                    self._make_path_segment_compatible(metadata.Author),
                                    self._make_path_segment_compatible(metadata.Series),
                                    self._make_path_segment_compatible(metadata.Title)
                                    )

        if createfolders:
            if not dryrun:
                if confirm_action:
                    ui.info("Folder Structure:", fullpath)
                    yn = ui.ask_yes_no("Should I create the folder structure?", default=True)
                    if yn:
                        Path(fullpath).mkdir(parents=True, exist_ok=True)
                else:
                    ui.info("Creating folders:", fullpath)
                    Path(fullpath).mkdir(parents=True, exist_ok=True)
            else:
                ui.warning(ui.bold, "[DRYRUN]", ui.reset, "Creating folderstructure", ui.bold, fullpath)

        if save_cover and move is not False:
            if not dryrun:
                if confirm_action:
                    yn = ui.ask_yes_no("Should I export cover image?", default=True)
                    if yn:
                        metadata.export_cover(fullpath, case_sensitive=True)  # save cover file
                else:
                    metadata.export_cover(fullpath, case_sensitive=True)  # save cover file

                ui.info("Saving cover to", ui.bold, fullpath + "/cover.jpg")
            else:
                ui.warning(ui.bold, "[DRYRUN]", ui.reset, "Saving cover to", ui.bold, fullpath + "cover.jpg")


        if not createfolders or not move:
            ui.info("No moving or copying")
        else:
            if move:
                if not dryrun:
                    ui.warning("moving ", ui.bold, os.path.join(path, file), ui.reset, "-->", ui.green,
                               os.path.join(fullpath, file))
                    os.rename(os.path.join(path, file), os.path.join(fullpath, file))
                else:
                    ui.warning("[DRYRUN] move ", ui.bold, os.path.join(path, file), ui.reset, "-->", ui.green, os.path.join(fullpath, file))
            else:
                import shutil
                if not dryrun:
                    shutil.copy2(os.path.join(path, file), os.path.join(fullpath, file))
                else:
                    ui.warning("[DRYRUN] copy ", ui.bold, os.path.join(path, file), ui.reset, "-->", ui.green,
                           os.path.join(fullpath, file))

    def _iterate_files(self, files, callback):
        for file in files:
            pass

    def _get_folders_from_path(self, root, path):
        folder = root.replace(path + "\\", "")
        return get_folders_from_path(folder)

    def organize(self, dryrun=False, confirm_action=True, outpath=""):
        default_path = "\\\\10.1.1.210\\media\\audio\\audio_books"
        default_path = "C:\\Users\\Vital\\OpenAudible\\books"
        default_path = "C:\\PyCharmProjects\\googlebooks\\data"
        default_path = "\\\\10.1.1.210\\media\\audio\\audio_books"
        # default_output = None
        default_output = "\\\\10.1.1.210\\media\\audio\\audiobooks_organized"

        path = ui.ask_string("Enter path to your audiobooks", default=default_path)
        output = ui.ask_string("Enter path to your output directory", default=default_output)
        dryrun = ui.ask_yes_no("Should we enable dry run?", default=True)
        confirm_action = ui.ask_yes_no("Do you wanna confirm every action I suggest?", default=True)

        writetags = ui.ask_yes_no("Should I write the tags to file?", default=True)
        createfolders = ui.ask_yes_no("Should I create the new folder structure?", default=True)
        move = ui.ask_yes_no("Should I move the files?", default=True)

        ui.info("Checking tags in", ui.bold, path)
        self._walk_path(path,
                        output=output,
                        dryrun=dryrun,
                        confirm_action=confirm_action,
                        writetags=writetags,
                        createfolders=createfolders,
                        move=move
                        )

        # output = None, dryrun = True, confirm_action = True, writetags = True, createfolders = True, move = True

    def run(self):
        ui.setup(color="always")
        ui.info("Welcome to", ui.bold, ui.red, "AudioBookOrganizer v" + App._VERSION)
        self.main_menu()
