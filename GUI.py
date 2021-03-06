import wx
import Crawler
from PaperInfo import Paper, Pair
import DownloadModule
import Cache
import os
import time
import platform
import subprocess


def on_preferences(event):
    preferences_frame = PreferencesFrame()
    preferences_frame.Show()


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Past paper Crawler", size=(510, 585))

        self.level_list = ["--- Select level ---", "IGCSE", "AS & A-Level", "O-Level"]
        self.type_list = []
        self.subject_dict = {}  # A dictionary of subjects available return from Crawler. (key: subject name, value: subject url)
        self.paper_dict = {}  # A dictionary of papers available return from Crawler. (key: f_in name, [value]: paper ur)
        self.paired = True

        self.retry_urls = []  # List of url need to retry download
        self.directory = ""  # Record the root folder the user choose to save the f_in
        self.year, self.season, self.num, self.region, self.type = "All years", "All seasons", "All papers", "All regions", "All types"  # Record the subject, season, num, region, chosen by the user

        self.pairs_list, self.pairs_info = [], {}  # Store the information of question paper and corresponding mark scheme
        self.files_list, self.files_info = [], {}  # Store the information of each individual f_in

        self.level_choice = wx.Choice(self, choices=self.level_list)  # Choosing the level
        self.level_choice.SetSelection(0)
        self.level_choice.Bind(wx.EVT_CHOICE, self.level_chosen)

        self.subject_choice = wx.Choice(self)  # Choosing the subject
        self.subject_choice.Bind(wx.EVT_CHOICE, self.subject_chosen)

        self.year_choice = wx.Choice(self, size=(85, 25))  # Choosing the year
        self.year_choice.Bind(wx.EVT_CHOICE, self.year_chosen)

        self.season_choice = wx.Choice(self, size=(85, 25))  # Choosing the season
        self.season_choice.Bind(wx.EVT_CHOICE, self.season_chosen)

        self.num_choice = wx.Choice(self, size=(85, 25))  # Choosing the paper number
        self.num_choice.Bind(wx.EVT_CHOICE, self.num_chosen)

        self.region_choice = wx.Choice(self, size=(85, 25))  # Choosing the region
        self.region_choice.Bind(wx.EVT_CHOICE, self.region_chosen)

        txt_filter = wx.StaticText(self, label="Filter:")
        self.style_choice = wx.Choice(self, size=(160, 25))  # Choosing the display style
        self.style_choice.Bind(wx.EVT_CHOICE, self.style_chosen)
        self.hint = wx.StaticText(self, label="Papers and answers before 2005 are omitting.")

        download = wx.Button(self, label="Download", size=(60, 25))  # Download button
        self.Bind(wx.EVT_BUTTON, self.pre_download, download)

        self.type_choice = wx.Choice(self, size=(40, 25))
        self.type_choice.Bind(wx.EVT_CHOICE, self.type_chosen)
        self.type_choice.Hide()

        self.paper_checklist = wx.CheckListBox(self)  # Check list box to display papers avaliable for downloading

        select_all = wx.Button(self, label="Select All", size=(60, 25))  # Select all button
        self.Bind(wx.EVT_BUTTON, self.select_all, select_all)

        # Arranging boxes

        sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        sizer_filter = wx.BoxSizer(wx.HORIZONTAL)
        sizer_paper_checklist = wx.BoxSizer(wx.HORIZONTAL)
        sizer_hint = wx.BoxSizer(wx.HORIZONTAL)
        sizer_bottom = wx.BoxSizer(wx.HORIZONTAL)

        bottom_border = 10

        sizer_top.Add(self.level_choice, proportion=1, flag=wx.BOTTOM | wx.RIGHT, border=bottom_border | 5)
        sizer_top.Add(self.subject_choice, proportion=1, flag=wx.ALIGN_RIGHT | wx.BOTTOM, border=bottom_border)

        sizer_filter.Add(txt_filter, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, border=bottom_border)
        sizer_filter.Add(self.year_choice, proportion=1, flag=wx.LEFT | wx.BOTTOM, border=10 | bottom_border)
        sizer_filter.Add(self.season_choice, proportion=1, flag=wx.LEFT | wx.BOTTOM, border=10 | bottom_border)
        sizer_filter.Add(self.num_choice, proportion=1, flag=wx.LEFT | wx.BOTTOM, border=10 | bottom_border)
        sizer_filter.Add(self.region_choice, proportion=1, flag=wx.LEFT | wx.BOTTOM, border=10 | bottom_border)

        sizer_paper_checklist.Add(self.paper_checklist, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=bottom_border)

        sizer_hint.Add(self.hint, proportion=0, flag=wx.BOTTOM, border=bottom_border)

        sizer_bottom.Add(self.style_choice, proportion=1, flag=wx.ALIGN_LEFT)
        sizer_bottom.Add(self.type_choice, proportion=1, flag=wx.LEFT | wx.RESERVE_SPACE_EVEN_IF_HIDDEN, border=5)
        sizer_bottom.Add(select_all, proportion=1, flag=wx.LEFT, border=15)
        sizer_bottom.Add(download, proportion=1, flag=wx.ALIGN_RIGHT | wx.LEFT, border=5)

        sizer_all = wx.BoxSizer(wx.VERTICAL)
        side_border = 25

        sizer_all.Add(sizer_top, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=side_border|side_border|1)
        sizer_all.Add(sizer_filter, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=side_border|side_border)
        sizer_all.Add(sizer_paper_checklist, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=side_border | side_border)
        sizer_all.Add(sizer_hint, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=side_border|side_border)
        sizer_all.Add(sizer_bottom, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=side_border|side_border|1)

        self.SetSizer(sizer_all)

        # initialize menu
        menu_bar = wx.MenuBar()
        menu = wx.Menu()

        self.about = wx.MenuItem(menu, wx.ID_ABOUT, "About Past Paper Crawler")
        self.Bind(wx.EVT_MENU, self.on_about, self.about)
        menu.Append(self.about)

        preferences = wx.MenuItem(menu, wx.ID_PREFERENCES, '&Preferences...\tCtrl+,')
        self.Bind(wx.EVT_MENU, on_preferences, preferences)
        menu.Append(preferences)

        # For different system
        if platform.system() == "Darwin":
            menu_bar.Append(menu, " ")
        else:
            menu_bar.Append(menu, "File")

        self.SetMenuBar(menu_bar)

    def on_about(self, event):
        about_frame = AboutFrame(self.rebind_about)
        about_frame.Show()
        self.Unbind(wx.EVT_MENU, self.about)

    def rebind_about(self):
        self.Bind(wx.EVT_MENU, self.on_about, self.about)

    def level_chosen(self, event):
        level = self.level_choice.GetStringSelection()  # Get level chosen
        self.subject_choice.Clear()
        self.paper_checklist.Clear()
        self.year_choice.Clear()
        self.season_choice.Clear()
        self.num_choice.Clear()
        self.region_choice.Clear()
        self.pairs_info = {}
        self.files_info = {}

        if level == self.level_list[0]:  # Not choosing a level
            return

        # Cache
        global cache_folder
        cache_subject = os.path.join(cache_folder, "GCE Guide %s" % level)
        if not os.path.exists(cache_subject):
            self.subject_dict = Crawler.visit_level(Crawler.levels_dict[level])  # Return subject list
            if self.subject_dict == -1:  # Connection error
                wx.MessageBox("Please check your Internet connection and retry.", "Connection Error")
                self.level_choice.SetSelection(0)
                return
            else:
                Cache.store(self.subject_dict, cache_subject)
        else:
            self.subject_dict = Cache.load(cache_subject)

        subject_list = ["----- Select subject -----"] + [each for each in self.subject_dict]
        self.subject_choice.Set(subject_list)  # Update subject list
        self.subject_choice.SetSelection(0)

    def subject_chosen(self, event):
        subject = self.subject_choice.GetStringSelection()  # Get subject chosen
        self.paper_checklist.Clear()
        self.year_choice.Clear()
        self.season_choice.Clear()
        self.num_choice.Clear()
        self.region_choice.Clear()
        self.pairs_info = {}
        self.files_info = {}

        # If no subject is chosen
        try:
            subject_url = self.subject_dict[subject]
        except KeyError:
            return

        # Cache
        global cache_folder
        cache_paper = os.path.join(cache_folder, "GCE Guide %s" % subject)
        if not os.path.exists(cache_paper):
            self.paper_dict = Crawler.visit_subject(subject_url)  # Get paper list
            if self.paper_dict == -1:  # Connection error
                wx.MessageBox("Please check your Internet connection and retry.", "Connection Error")
                self.subject_choice.SetSelection(0)
                return
            else:
                Cache.store(self.paper_dict, cache_paper)
        else:
            self.paper_dict = Cache.load(cache_paper)

        sorted_file = sorted(self.paper_dict)
        qp, ms = [], []  # Store question paper and mark scheme for pairing

        years, nums, regions, types = [], [], [], []  # Store all exist year, paper number, and region

        for file in sorted_file:
            paper = Paper(file, self.paper_dict[file])
            if paper.year != "other" and int(paper.year) > 2004:
                if paper.type == "qp":
                    qp.append(paper)
                elif paper.type == "ms":
                    ms.append(paper)

            self.files_info[file] = paper
            years.append(paper.year)
            nums.append(paper.num)
            regions.append(paper.region)
            if paper.type != "other" and paper.type != "qp" and paper.type != "ms":
                types.append(paper.type)

        year_list = ["All years"] + sorted(list(set(years)))
        season_list = ("All seasons", "March", "May/June", "November", "other")
        num_list = ["All papers"] + sorted(list(set(nums)))
        region_list = ["All regions"] + sorted(list(set(regions)))
        self.type_list = ["All types", "qp", "ms"] + sorted(list(set(types))) + ["other"]

        for i in range(len(qp)):
            for each in ms:
                if qp[i].year == each.year and qp[i].season == each.season and qp[i].num == each.num and qp[i].region == each.region:
                    pair = Pair(qp[i], each)
                    del each
                    self.pairs_info[pair.display()] = pair
                    break

        self.pairs_list = [each for each in self.pairs_info]  # Store the name of the pairing files for display
        self.files_list = [each for each in self.files_info]  # Store the name of the individual files for display

        self.year_choice.Set(year_list)
        self.year_choice.SetSelection(0)
        self.season_choice.Set(season_list)
        self.season_choice.SetSelection(0)
        self.num_choice.Set(num_list)
        self.num_choice.SetSelection(0)
        self.region_choice.Set(region_list)
        self.region_choice.SetSelection(0)

        self.style_choice.Set(["Select All QP & MS in pairs", "Select all individual files"])
        self.style_choice.SetSelection(0)
        self.style_chosen(None)

        if self.paired:  # Display information according to the display style
            self.paper_checklist.Set(self.pairs_list)
        else:
            self.paper_checklist.Set(self.files_list)

    def year_chosen(self, event):  # when year is chosen
        self.year = self.year_choice.GetStringSelection()
        if self.paired:
            self.filter_pairs()
        else:
            self.filter_files()

    def season_chosen(self, event):  # when season is chosen
        self.season = self.season_choice.GetStringSelection()
        if self.paired:
            self.filter_pairs()
        else:
            self.filter_files()

    def num_chosen(self, event):  # when paper number is chosen
        self.num = self.num_choice.GetStringSelection()
        if self.paired:
            self.filter_pairs()
        else:
            self.filter_files()

    def region_chosen(self, event):  # when region is chosen
        self.region = self.region_choice.GetStringSelection()
        if self.paired:
            self.filter_pairs()
        else:
            self.filter_files()

    def type_chosen(self, event):
        self.type = self.type_choice.GetStringSelection()
        self.filter_files()

    def filter_files(self):  # filter individual files which meet the requirement
        to_filter = self.files_info.copy()
        if self.year != "All years":
            to_filter = {file_name: file_object for file_name, file_object in to_filter.items() if
                         file_object.year == self.year}
        if self.season != "All seasons":
            to_filter = {file_name: file_object for file_name, file_object in to_filter.items() if
                         file_object.season == self.season}
        if self.num != "All papers":
            to_filter = {file_name: file_object for file_name, file_object in to_filter.items() if
                         file_object.num == self.num}
        if self.region != "All regions":
            to_filter = {file_name: file_object for file_name, file_object in to_filter.items() if
                         file_object.region == self.region}
        if self.type != "All types":
            to_filter = {file_name: file_object for file_name, file_object in to_filter.items() if
                         file_object.type == self.type}

        self.files_list = [file for file in to_filter]
        self.paper_checklist.Set(self.files_list)

    def filter_pairs(self):  # filter paired files which meet the requirement
        to_filter = self.pairs_info.copy()
        if self.year != "All years":
            to_filter = {pair_name: pair_object for pair_name, pair_object in to_filter.items() if
                         pair_object.year == self.year}
        if self.season != "All seasons":
            to_filter = {pair_name: pair_object for pair_name, pair_object in to_filter.items() if
                         pair_object.season == self.season}
        if self.num != "All papers":
            to_filter = {pair_name: pair_object for pair_name, pair_object in to_filter.items() if
                         pair_object.num == self.num}
        if self.region != "All regions":
            to_filter = {pair_name: pair_object for pair_name, pair_object in to_filter.items() if
                         pair_object.region == self.region}

        self.pairs_list = [pair for pair in to_filter]
        self.paper_checklist.Set(self.pairs_list)

    def style_chosen(self, event):  # when display style was chosen
        self.paired = True if self.style_choice.GetSelection() == 0 else False
        if self.paired:
            self.hint.SetLabel("Papers and answers before 2005 are omitted.")
            self.type_choice.Hide()
            self.filter_pairs()
        else:
            self.hint.SetLabel("All files are shown.")
            self.filter_files()
            self.type_choice.Set(self.type_list)
            self.type_choice.Show()

    def select_all(self, event):  # when select all is pressed
        if self.paired:
            if len(self.paper_checklist.GetCheckedItems()) != len(self.pairs_list):
                self.paper_checklist.SetCheckedItems(range(len(self.pairs_list)))
            else:
                for i in range(len(self.pairs_list)):
                    self.paper_checklist.Check(i, check=False)
        else:
            if len(self.paper_checklist.GetCheckedItems()) != len(self.files_list):
                self.paper_checklist.SetCheckedItems(range(len(self.files_list)))
            else:
                for i in range(len(self.files_list)):
                    self.paper_checklist.Check(i, check=False)

    def pre_download(self, event):
        dlg = wx.DirDialog(self, "Choose the root folder for past paper")
        if dlg.ShowModal() == wx.ID_OK:
            folder_directory = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

        self.directory = os.path.join(folder_directory, self.subject_choice.GetStringSelection())
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        selected_paper = self.paper_checklist.GetCheckedStrings()
        if not selected_paper:
            return

        urls = []
        if self.paired:
            for each in selected_paper:
                urls.append(self.pairs_info[each].url[0])
                urls.append(self.pairs_info[each].url[1])
        else:
            for each in selected_paper:
                urls.append(self.files_info[each].url)

        self.download(urls)

    def download(self, urls):  # when download button is pressed
        total_files = len(urls)
        DownloadModule.download_thread(urls, self.directory)

        # Show progress
        progress_bar = wx.ProgressDialog("Progress", "Start downloading files", maximum=total_files,
                                         style=wx.PD_CAN_ABORT)
        time.sleep(1)
        while DownloadModule.running:
            if progress_bar.WasCancelled():
                DownloadModule.control = 1
                progress_bar.Destroy()
                wx.MessageBox("Download is cancelled.")
                break

            status = DownloadModule.status
            progress_bar.Update(status['F'], "Finish downloading %d/%d files" % (status['F'], total_files))
            time.sleep(1)

        error_files = DownloadModule.failed_names
        # selected_paper = self.paper_checklist.GetCheckedItems()
        if error_files:
            progress_bar.Destroy()
            retry_frame = RetryFrame(self, error_files, self.call_back)
            retry_frame.ShowModal()

            # for each in selected_paper:
            #     if each not in error_files:
            #         self.paper_checklist.Check(each, check=False)
        else:
            progress_bar.Update(total_files)
            # for each in selected_paper:
            #     self.paper_checklist.Check(each, check=False)

    def call_back(self, value):  # Link with RetryFrame
        if value:
            self.retry_urls = [self.paper_dict[each] for each in value]
            self.download(self.retry_urls)


class RetryFrame(wx.Dialog):  # New frame to display f_in that need to retry
    def __init__(self, parent, retry_files, call):
        wx.Dialog.__init__(self, parent, -1, size=(300, 340))
        wx.StaticText(self, pos=(15, 10), label="Failed to download:")
        self.retry_file = wx.CheckListBox(self, -1, pos=(15, 30), size=(270, 250), choices=retry_files)
        self.retry_file.SetCheckedItems(range(len(retry_files)))
        retry_button = wx.Button(self, -1, pos=(210, 285), size=(75, 20), label="Retry")
        retry_button.Bind(wx.EVT_BUTTON, self.retry, retry_button)

        self.call = call

    def retry(self, event):
        self.Destroy()
        self.call(self.retry_file.GetCheckedStrings())


class AboutFrame(wx.Frame):
    def __init__(self, call):
        wx.Frame.__init__(self, None, -1, size=(300, 160), style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)

        title = wx.StaticText(self, label="Past Paper Crawler")
        title_font = wx.Font(wx.FontInfo(13).Bold().FaceName("Arial"))
        title.SetFont(title_font)

        version = wx.StaticText(self, label="Version 1.2.2")
        team = wx.StaticText(self, label="Made by Teresa, John, Ethan, and Peter")
        maintenance = wx.StaticText(self, label="Currently maintained by Teresa")
        thanks = wx.StaticText(self, label="Inspired by Past Paper Crawler created by Raymond")

        content_font = wx.Font(wx.FontInfo(10))
        version.SetFont(content_font)
        team.SetFont(content_font)
        maintenance.SetFont(content_font)
        thanks.SetFont(content_font)

        bottom_border = 10
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(title, flag=wx.ALIGN_CENTER | wx.BOTTOM | wx.TOP, border=bottom_border | bottom_border)
        sizer.Add(version, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=bottom_border)
        sizer.Add(team, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=bottom_border)
        sizer.Add(maintenance, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=bottom_border)
        sizer.Add(thanks, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=bottom_border)

        self.SetSizer(sizer)

        self.call = call
        self.Bind(wx.EVT_CLOSE, self.on_close, self)

    def on_close(self, event):
        self.Destroy()
        self.call()


class PreferencesFrame(wx.Frame):
    def __init__(self):
        # wx.Frame.__init__(self, None, style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)
        wx.Frame.__init__(self, None)
        self.init_UI()

    def init_UI(self):
        preference = wx.Notebook(self)
        preference.AddPage(GeneralPanel(preference), "General")
        preference.AddPage(CachePanel(preference), "Cache")
        self.Show()

    
class GeneralPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)


class CachePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        explain_txt = wx.StaticText(self, label="Past Paper Crawler caches viewed web pages to memory and disk to boost efficiency.")
        hint_txt = wx.StaticText(self, label="Current cache on the disk:")
        open_button = wx.Button(self, label="open folder")
        self.Bind(wx.EVT_BUTTON, self.on_open, open_button)

        global cache_folder
        cache_list = os.listdir(cache_folder)
        cache_checklist = wx.CheckListBox(self, choices=cache_list)

        open_cache_sizer = wx.BoxSizer(wx.HORIZONTAL)
        open_cache_sizer.Add(hint_txt)
        open_cache_sizer.Add(open_button)

        cache_sizer = wx.BoxSizer(wx.VERTICAL)
        cache_sizer.Add(explain_txt, flag=wx.BOTTOM, border=10)
        cache_sizer.Add(open_cache_sizer, flag=wx.BOTTOM, border=10)
        cache_sizer.Add(cache_checklist, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, border=10)
        self.SetSizer(cache_sizer)

    @staticmethod
    def on_open(event):
        global cache_folder
        if platform.system() == "Darwin":
            subprocess.call(["open", cache_folder])
        else:
            subprocess.Popen("explorer %s" % cache_folder)


cache_folder = Cache.get_cache_directory()

if __name__ == '__main__':

    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
