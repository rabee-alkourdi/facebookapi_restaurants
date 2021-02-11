import tkinter as tk
from tkinter import filedialog 
from tkinter import messagebox
import pygubu
import os
from helper import Facebook_Helper as fh
import pandas as pd
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

class Facebook_Main:

    def __init__(self):
        self.dataset = pd.DataFrame
        self.fields = []
        self.selectedFields = []
        self.remainingFields = []

        self.qterms = []
        
    def mainGUI(self, root):
        root.title("Rabee's Facebook Analytics")
        root.resizable(False, False)
        self.builder = pygubu.Builder() # Create a builder
        self.builder.add_from_file('gui\\MainGUI.ui') # Load an ui file
        self.mainwindow = self.builder.get_object('mainGUI', root) # Create the widget using a master as parent
        self.console = self.builder.get_object('consoleTxt', root)
        self.builder.connect_callbacks(self)
        self.saveBtn = self.builder.get_object('saveBtn', root)
              
        # Disable all unuasable buttons initially
        self.enableButton(self.saveBtn, False)
        self.statsFrame = self.builder.get_object('statsFrm', root)
        for child in self.statsFrame.winfo_children():
            try:
                child.config(state='disable')
            except:
                continue
        
        # Initialize Console scrollbars
        consoleVScrollbar = self.builder.get_object('consoleVScrlBr', root)
        self.console.config(yscrollcommand=consoleVScrollbar.set)
        consoleVScrollbar.config(command=self.console.yview)
        consoleHScrollbar = self.builder.get_object('consoleHScrlBr', root)
        self.console.config(xscrollcommand=consoleHScrollbar.set)
        consoleHScrollbar.config(command=self.console.xview)
   
    def enableButton(self, button_handler, enable):
        if enable:
            button_handler.configure(state='normal')
        else:
            button_handler.configure(state='disable')
   
    # Data Fetch functions --------------------------------------------- # 
    def fetchBtnAction(self):
        self.fetch_root = tk.Tk()
        self.fetch_root.title("Fetch Data Online")
        self.fetch_root.resizable(False, False)
        self.fetch_builder = pygubu.Builder() # Create a builder
        self.fetch_builder.add_from_file('gui\\FetchGUI.ui') # Load an ui file
        self.fetch_mainwindow = self.fetch_builder.get_object('fetchGUI', self.fetch_root) # Create the widget using a master as parent
        self.fetch_builder.connect_callbacks(self)
        self.initializeFieldsLists()
        
        self.fetch_root.grab_set() # Disable underlaying frames
        
    def initializeFieldsLists(self):
        self.sourceList = self.fetch_builder.get_object('sourceLst', root)
        self.destinationList = self.fetch_builder.get_object('destinationLst', root)

        fields_elements = ET.parse('files\\Config files\\fields.xml').getroot()
        for field in fields_elements:
            self.fields += [field.text]
        self.sourceList.insert("end", *self.fields)
        self.remainingFields = self.fields

        sourceScrollbar = self.fetch_builder.get_object('sourceScrlBr', root)
        self.sourceList.config(yscrollcommand=sourceScrollbar.set)
        sourceScrollbar.config(command=self.sourceList.yview)

        destinationScrollbar = self.fetch_builder.get_object('destinationScrlBr', root)
        self.destinationList.config(yscrollcommand=destinationScrollbar.set)
        destinationScrollbar.config(command=self.destinationList.yview)
    
    def listAddBtnAction(self):
        self.selectedFields += [self.sourceList.get(idx) for idx in self.sourceList.curselection()]
        self.remainingFields = [v for i,v in enumerate(self.remainingFields) if i not in self.sourceList.curselection()] 
        self.updateFieldsLists()
        
    def listAddAllBtnAction(self):
        self.sourceList.delete(0, "end")
        self.remainingFields = []

        self.destinationList.delete(0, "end")
        self.selectedFields = self.fields
        self.destinationList.insert("end", *self.selectedFields)

    def listRemoveBtnAction(self):
        self.remainingFields += [self.destinationList.get(idx) for idx in self.destinationList.curselection()]
        self.selectedFields = [v for i,v in enumerate(self.selectedFields) if i not in self.destinationList.curselection()] 
        self.updateFieldsLists()

    def listRemoveAllBtnAction(self):
        self.sourceList.delete(0, "end")
        self.remainingFields = self.fields
        self.sourceList.insert("end", *self.remainingFields)

        self.destinationList.delete(0, "end")
        self.selectedFields = []

    def updateFieldsLists(self):
        self.destinationList.delete(0, "end")
        self.selectedFields.sort()
        self.destinationList.insert("end", *self.selectedFields)

        self.sourceList.delete(0, "end")
        self.remainingFields.sort()
        self.sourceList.insert("end", *self.remainingFields)

    def loadQueryTermsBtnAction(self):
        ftypes = [('Extended Markup Language files', '*.xml')]
        filePath = filedialog.askopenfilename(initialdir = ".\\files\\Config files", title = "Select query terms file", filetypes=ftypes)
        if filePath:
            qterms_elements = ET.parse(filePath).getroot()
            for qterm in qterms_elements:
                self.qterms += [qterm.text]

            queryObj = self.fetch_builder.get_object('qtermsTxt', root)
            qtermsSTR = ','.join(self.qterms)
            queryObj.delete(1.0, "end")
            queryObj.insert("end", qtermsSTR)
        else:
            print('cancelled')

    def fetchDataBtnAction(self):
        queryObj = self.fetch_builder.get_object('qtermsTxt', root)
        selected_qterms = queryObj.get("1.0",'end-1c')
        self.qterms = selected_qterms.split(',')

        tokenObj = self.fetch_builder.get_object('tokenTxt', root)
        buttonObj = self.fetch_builder.get_object('fetchDBtn', root)
        self.token = tokenObj.get("1.0",'end-1c')
        
        buttonObj.configure(text='Fetching....')
        self.mainwindow.configure(cursor='wait')

        unprocessed_data = fh.fetchOnlineData(self.token, self.selectedFields, self.qterms)
        messagebox.showinfo('Message', 'Fetched {0} records.'.format(len(unprocessed_data)))

        filePath = filedialog.asksaveasfilename(initialdir = ".\\files\\RAW files", 
                                            title = "Choose where to save the raw data file", 
                                            filetypes=[("JavaScript Object Notation file","*.json*")])
        if filePath:
            fh.rawJsonRW(filePath, 'w', unprocessed_data) # Dump raw data to json file
            messagebox.showinfo('Message', 'File saved successfully. Wrote {0} records.'.format(len(unprocessed_data)))

            self.mainwindow.configure(cursor='arrow')
            self.fetch_root.grab_release() #Enable underlaying frames
            self.fetch_root.destroy()
        else:
            print('cancelled')      
    # ------------------------------------------------------------------ #

    # Preparing & I/O functions ---------------------------------------- # 
    def prepareDataBtnAction(self):
        ftypes = [('JavaScript Object Notation files', '*.json')]
        filePath = filedialog.askopenfilename(initialdir = ".\\files\\RAW files", title = "Select raw data file", filetypes=ftypes)
        if filePath:
            unprocessed_data = fh.rawJsonRW(filePath, 'r')
            
            root.configure(cursor='wait')
            root.grab_set()

            final_fields = ['id', 'name', 'fan_count', 'overall_star_rating', 'restaurant_services',
                       'category', 'restaurant_specialties', 'price_range', 'talking_about_count', 'checkins']

            final_services = ["delivery", "reserve", "waiter"]
            reduced_data = fh.selectAndFill(final_fields, ['restaurant_services'], [final_services], unprocessed_data)
            self.dataset = fh.convertToDF(reduced_data)

            messagebox.showinfo('Message', 'Finished preparing data. Prepared {0} records.'.format(len(self.dataset)))
            self.enableButton(self.saveBtn, True)
            for child in self.statsFrame.winfo_children():
                try:
                    child.config(state='normal')
                except:
                    continue

            root.grab_release()
            root.configure(cursor='arrow')
        else:
            print('cancelled')
  
    def saveFileBtnAction(self):
        filePath = filedialog.asksaveasfilename(initialdir = ".\\files\\Processed files", 
                                            title = "Choose where to save dataset file", 
                                            filetypes=[("all files","*.*")])
        if filePath:
            fileType = os.path.splitext(filePath)[1]
            fh.writeToFile(filePath, fileType[1:], self.dataset)
            messagebox.showinfo('Message', 'File saved successfully. Wrote {0} records.'.format(len(self.dataset)))
        else:
            print('cancelled')

    def loadFileBtnAction(self):
        ftypes = [
            ('Comma-Separated Values files', '*.csv'),
            ('Excel Microsoft Office Open XML Format Spreadsheet files', '*.xlsx'),
            ('JavaScript Object Notation files', '*.json')
        ]
        filePath = filedialog.askopenfilename(initialdir = ".\\files\\Processed files", title = "Select dataset file", filetypes=ftypes)
        if filePath:
            fileType = os.path.splitext(filePath)[1]
            self.dataset = fh.readFile(filePath, fileType[1:])
            messagebox.showinfo('Message', 'Dataset read successfully. Read {0} records.'.format(len(self.dataset)))

            self.dataset = self.dataset.set_index('id')
            self.enableButton(self.saveBtn, True)
            for child in self.statsFrame.winfo_children():
                try:
                    child.config(state='normal')
                except:
                    continue
        else:
            print('cancelled')
    # ------------------------------------------------------------------ #
             
    # General Info functions ------------------------------------------- #  
    def generalInfoBtnAction(self): 
        self.console.configure(state='normal')

        types_info = str(self.dataset.dtypes)
        index_info = str(self.dataset.index)
        ds_info = str(self.dataset.describe())

        self.console.configure(state='normal')
        self.console.delete(1.0, "end")
        self.console.insert("end", "Dataset Fields Info---------------------------------------------+\n")
        self.console.insert("end", types_info)
        self.console.insert("end", "\n+---------------------------------------------------------------+\n")
        self.console.insert("end", "\nDataset Index Info----------------------------------------------+\n")
        self.console.insert("end", index_info)
        self.console.insert("end", "\n+---------------------------------------------------------------+\n")
        self.console.insert("end", "\nDataset Numeric Fields Info-------------------------------------+\n")
        self.console.insert("end", ds_info)
        self.console.insert("end", "\n+---------------------------------------------------------------+\n")

        self.console.configure(state='disable')
    # ------------------------------------------------------------------ #

    # Sort & Display functions ----------------------------------------- # 
    def shuffleBtnAction(self):
        self.dataset = self.dataset.sample(frac=1)
        messagebox.showinfo('Message', 'Dataset has been shuffled')

    def sortByBtnAction(self):
        self.sb_root = tk.Tk()
        self.sb_root.title("Sort By")
        self.sb_root.resizable(False, False)
        self.sb_builder = pygubu.Builder() # Create a builder
        self.sb_builder.add_from_file('gui\\SortByGUI.ui') # Load an ui file
        self.sb_mainwindow = self.sb_builder.get_object('sortByFrm', self.sb_root) # Create the widget using a master as parent
        self.sb_builder.connect_callbacks(self)

        self.dataset = self.dataset.reset_index()
        self.numComboBox = self.sb_builder.get_object('numCmbBx', self.sb_root)
        self.numComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))

    def sortByOkBtnAction(self):
        self.ascBtn = self.sb_builder.get_object('sortAscRBtn', self.sb_root)
        selected_field = self.numComboBox.get()
        if selected_field: 
            if 'selected' in self.ascBtn.state():
                asc = True
            else:
                asc = False

            sorted_dataset = self.dataset.sort_values(by=[selected_field], ascending=[asc])
            self.dataset = sorted_dataset.set_index('id')
            self.sb_root.destroy()
        else:
            messagebox.showerror('Message', 'No field was selected')

    def displayNBtnAction(self):
        nEntry = self.builder.get_object('nEnt', root)
        try:
            n = int(nEntry.get())
            if n > 0:
                pd.set_option('display.width', 5000)
                pd.set_option('display.max_rows', 1000)
                self.console.configure(state='normal')
                self.console.delete(1.0, "end")
                self.console.insert("end", self.dataset.head(n))
                self.console.insert("end", "\n+-----------------------------------------------------------------+\n")
                self.console.configure(state='disable')
            else:
                messagebox.showerror('Message', 'Enter a valid N value')
        except:
            print('error')        
    # ------------------------------------------------------------------ #

    # GroupBy functions ------------------------------------------------ #
    def groupByBtnAction(self):
        self.gb_root = tk.Tk()
        self.gb_root.title("Group By")
        self.gb_root.resizable(False, False)
        self.gb_builder = pygubu.Builder() # Create a builder
        self.gb_builder.add_from_file('gui\\GroupByGUI.ui') # Load an ui file
        self.gb_mainwindow = self.gb_builder.get_object('groupByFrm', self.gb_root) # Create the widget using a master as parent
        self.gb_builder.connect_callbacks(self)

        self.catsComboBox = self.gb_builder.get_object('catCmbBx', self.gb_root)
        self.catsComboBox['values'] = list(self.dataset.select_dtypes(include=['category', 'bool']))
            
    def groupByOkBtnAction(self):
        selected_category = self.catsComboBox.get()
        if selected_category:
            self.gb_root.destroy()
            numerical_fields = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))
            self.groupByCat(selected_category, numerical_fields)
        else:
            messagebox.showerror('Message', 'No category was selected')

    def groupByCat(self, categorical_field, numerical_fields):
        cat_group_by = self.dataset.groupby(categorical_field)

        self.console.configure(state='normal')
        self.console.delete(1.0, "end")
        self.console.insert("end", "Group By Statistics---------------------------------------------+\n")
        for n_field in numerical_fields:
            self.console.insert("end", "\nMeans of {0} per {1}\n".format(n_field, cat_group_by[n_field].mean().round(3)))
            self.console.insert("end", "\n\nMin of {0} per {1}\n".format(n_field, cat_group_by[n_field].min()))
            self.console.insert("end", "\n\nMax of {0} per {1}\n".format(n_field, cat_group_by[n_field].max()))
            self.console.insert("end", "\n\nSTD of {0} per {1}\n".format(n_field, cat_group_by[n_field].std()))
            
            self.console.insert("end", "\n+-----------------------------------------------------------------+\n")
        self.console.configure(state='disable')

        for n_field in numerical_fields:
            plt.figure()
            ax = cat_group_by[n_field].sum().plot(kind="barh", fontsize=8)
            for p in ax.patches:
                ax.annotate("{:,}".format(int(p.get_width())), 
                            (p.get_x() + p.get_width(), p.get_y()), 
                            xytext=(2, 4), 
                            textcoords='offset points')
            plt.title('{0} per {1}'.format(' '.join(n_field.split('_')).title(), 
                                           ' '.join(categorical_field.split('_')).title()), 
                      fontsize=25, name = 'Times New Roman') 
        plt.show()
        plt.close()
    # ------------------------------------------------------------------ #

    # Box Plot functions ----------------------------------------------- #
    def boxPlotBtnAction(self):
        self.bp_root = tk.Tk()
        self.bp_root.title("Box Plot")
        self.bp_root.resizable(False, False)
        self.bp_builder = pygubu.Builder() # Create a builder
        self.bp_builder.add_from_file('gui\\BoxPlotGUI.ui') # Load an ui file
        self.bp_mainwindow = self.bp_builder.get_object('boxPlotFrm', self.bp_root) # Create the widget using a master as parent
        self.bp_builder.connect_callbacks(self)

        self.catsComboBox = self.bp_builder.get_object('catCmbBx', self.bp_root)
        self.numsComboBox = self.bp_builder.get_object('numCmbBx', self.bp_root)
        self.catsComboBox['values'] = list(self.dataset.select_dtypes(include=['category', 'bool']))
        self.numsComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))

    def boxPlotOkBtnAction(self):
        selected_category = self.catsComboBox.get()
        selected_numeric = self.numsComboBox.get()
        if selected_category:
            if selected_numeric:
                self.bp_root.destroy()
                self.boxPlot(selected_category, selected_numeric)
            else:
                messagebox.showerror('Message', 'No numerical field was selected')
        else:
            messagebox.showerror('Message', 'No category was selected')

    def boxPlot(self, selected_category, selected_numeric):
        self.dataset.boxplot(column=selected_numeric, by=selected_category)
        plt.xlabel(' '.join(selected_category.split('_')).title(), fontsize=14)
        plt.ylabel(' '.join(selected_numeric.split('_')).title() , fontsize=14) 
        plt.show()
        plt.close()
    # ------------------------------------------------------------------ #

    # Scatter Plot functions ------------------------------------------- #
    def scatterPlotBtnAction(self):
        self.sp_root = tk.Tk()
        self.sp_root.title("Scatter Plot")
        self.sp_root.resizable(False, False)
        self.sp_builder = pygubu.Builder() # Create a builder
        self.sp_builder.add_from_file('gui\\ScatterPlotGUI.ui') # Load an ui file
        self.sp_mainwindow = self.sp_builder.get_object('scatterPlotFrm', self.sp_root) # Create the widget using a master as parent
        self.sp_builder.connect_callbacks(self)

        self.nums1ComboBox = self.sp_builder.get_object('num1CmbBx', self.sp_root)
        self.nums2ComboBox = self.sp_builder.get_object('num2CmbBx', self.sp_root)
        self.nums1ComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))
        self.nums2ComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))

    def scatterPlotOkBtnAction(self):
        selected_numeric1 = self.nums1ComboBox.get()
        selected_numeric2 = self.nums2ComboBox.get()
        if selected_numeric1:
            if selected_numeric2:
                self.sp_root.destroy()
                self.scatterPlot(selected_numeric1, selected_numeric2)
            else:
                messagebox.showerror('Message', 'Not all fields were selected')
        else:
            messagebox.showerror('Message', 'Not all fields were selected')

    def scatterPlot(self, field1, field2):
        self.dataset.plot(kind="scatter", x=field1, y=field2, c='black', alpha=.3, grid=True)
        plt.xlabel(' '.join(field1.split('_')).title(), fontsize=14)
        plt.ylabel(' '.join(field2.split('_')).title() , fontsize=14) 
        plt.show()
        plt.close()
    # ------------------------------------------------------------------ #

    # Histogram functions ---------------------------------------------- #
    def histogramBtnAction(self):
        self.hist_root = tk.Tk()
        self.hist_root.title("Histogram")
        self.hist_root.resizable(False, False)
        self.hist_builder = pygubu.Builder() # Create a builder
        self.hist_builder.add_from_file('gui\\HistogramGUI.ui') # Load an ui file
        self.hist_mainwindow = self.hist_builder.get_object('histFrm', self.hist_root) # Create the widget using a master as parent
        self.hist_builder.connect_callbacks(self)

        self.numsComboBox = self.hist_builder.get_object('numsCmbBx', self.hist_root)
        self.numsComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))

        self.binsEntry = self.hist_builder.get_object('binsEnt', self.hist_root)

        self.hist_root.grab_set()

    def histogramOkBtnAction(self):
        selected_numeric = self.numsComboBox.get()
        if selected_numeric:
            try:
                binsV = int(self.binsEntry.get())
                if binsV > 0:
                    self.hist_root.grab_release()
                    self.hist_root.destroy()
                    self.histogramPlot(selected_numeric, binsV)
                else:
                    messagebox.showerror('Message', 'Enter a valid Bins value')
            except:
                print('error')
        else:
            messagebox.showerror('Message', 'No field was selected')

    def histogramPlot(self, field, binsV):
        self.dataset[field].hist(bins=binsV)
        plt.xlabel('{0} Bins'.format(' '.join(field.split('_')).title() , fontsize=14))
        plt.ylabel('{0}'.format(' '.join(field.split('_')).title() , fontsize=14) , fontsize=14)
        plt.title('Histogram of {0}'.format(' '.join(field.split('_')).title()),
                    fontsize=25,
                    name = 'Times New Roman')
        plt.show()
        plt.close() 
    # ------------------------------------------------------------------ #

    # Pearson Correlation functions ------------------------------------ #
    def pearsonBtnAction(self):
        self.pcr_root = tk.Tk()
        self.pcr_root.title("Relationship")
        self.pcr_root.resizable(False, False)
        self.pcr_builder = pygubu.Builder() # Create a builder
        self.pcr_builder.add_from_file('gui\\PCRGUI.ui') # Load an ui file
        self.pcr_mainwindow = self.pcr_builder.get_object('pcrFrm', self.pcr_root) # Create the widget using a master as parent
        self.pcr_builder.connect_callbacks(self)

        self.pcr_nums1ComboBox = self.pcr_builder.get_object('num1CmbBx', self.pcr_root)
        self.pcr_nums2ComboBox = self.pcr_builder.get_object('num2CmbBx', self.pcr_root)
        self.pcr_nums1ComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))
        self.pcr_nums2ComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))

        self.pcr_root.grab_set()

    def pcrOkBtnAction(self):
        selected_numeric1 = self.pcr_nums1ComboBox.get()
        selected_numeric2 = self.pcr_nums2ComboBox.get()
        if selected_numeric1:
            if selected_numeric2:
                self.pcr_root.grab_release()
                self.pcr_root.destroy()
                fh.relationship(selected_numeric2, selected_numeric1, self.dataset)
            else:
                messagebox.showerror('Message', 'Not all fields were selected')
        else:
            messagebox.showerror('Message', 'Not all fields were selected')
    # ------------------------------------------------------------------ #

    # Independent samples T-Test functions ----------------------------- #
    def independentTBtnAction(self):
        self.ind_root = tk.Tk()
        self.ind_root.title("Independent samples T-Test")
        self.ind_root.resizable(False, False)
        self.ind_builder = pygubu.Builder() # Create a builder
        self.ind_builder.add_from_file('gui\\IndependentTTestGUI.ui') # Load an ui file
        self.ind_mainwindow = self.ind_builder.get_object('independentFrm', self.ind_root) # Create the widget using a master as parent
        self.ind_builder.connect_callbacks(self)

        self.ind_numsComboBox = self.ind_builder.get_object('numsCmbBx', self.ind_root)
        self.ind_catsComboBox = self.ind_builder.get_object('catsCmbBx', self.ind_root)
        self.ind_numsComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))
        self.ind_catsComboBox['values'] = list(self.dataset.select_dtypes(include=['bool']))

        self.ind_root.grab_set()

    def independentTOkBtnAction(self):
        selected_category = self.ind_catsComboBox.get()
        selected_numeric = self.ind_numsComboBox.get()
        if selected_category:
            if selected_numeric:
                self.ind_root.grab_release()
                self.ind_root.destroy()
                result = fh.independent_ttest(selected_numeric, selected_category, self.dataset)
                self.console.configure(state='normal')
                self.console.delete(1.0, "end")
                self.console.insert("end", "Results of Independent samples T-Test-------------------------------+\n\n")
                self.console.insert("end", result)
                self.console.insert("end", "\n\n+-----------------------------------------------------------------+\n")
                self.console.configure(state='disable')
            else:
                messagebox.showerror('Message', 'No DV was selected')
        else:
            messagebox.showerror('Message', 'No IV was selected')
    # ------------------------------------------------------------------ #

    # ANOVA functions -------------------------------------------------- #
    def anovaBtnAction(self):
        self.anv_root = tk.Tk()
        self.anv_root.title("One-Way ANOVA")
        self.anv_root.resizable(False, False)
        self.anv_builder = pygubu.Builder() # Create a builder
        self.anv_builder.add_from_file('gui\\AnovaGUI.ui') # Load an ui file
        self.anv_mainwindow = self.anv_builder.get_object('anovaFrm', self.anv_root) # Create the widget using a master as parent
        self.anv_builder.connect_callbacks(self)

        self.anv_numsComboBox = self.anv_builder.get_object('numsCmbBx', self.anv_root)
        self.anv_catsComboBox = self.anv_builder.get_object('catsCmbBx', self.anv_root)
        self.anv_numsComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))
        self.anv_catsComboBox['values'] = list(self.dataset.select_dtypes(include=['category', 'bool']))

        self.anv_root.grab_set()

    def anovaOkBtnAction(self):
        selected_category = self.anv_catsComboBox.get()
        selected_numeric = self.anv_numsComboBox.get()
        if selected_category:
            if selected_numeric:
                self.anv_root.grab_release()
                self.anv_root.destroy()
                result = fh.oneway_anova(selected_numeric, selected_category, self.dataset)
                self.console.configure(state='normal')
                self.console.delete(1.0, "end")
                self.console.insert("end", "Results of One-Way ANOVA Test-----------------------------------------+\n\n")
                self.console.insert("end", result)
                self.console.insert("end", "\n\n+-----------------------------------------------------------------+\n")
                self.console.configure(state='disable')
            else:
                messagebox.showerror('Message', 'No DV was selected')
        else:
            messagebox.showerror('Message', 'No IV was selected')

    def anovaTwoBtnAction(self):
        self.anv2_root = tk.Tk()
        self.anv2_root.title("Two-Way ANOVA")
        self.anv2_root.resizable(False, False)
        self.anv2_builder = pygubu.Builder() # Create a builder
        self.anv2_builder.add_from_file('gui\\AnovaTwoGUI.ui') # Load an ui file
        self.anv2_mainwindow = self.anv2_builder.get_object('twoanovaFrm', self.anv2_root) # Create the widget using a master as parent
        self.anv2_builder.connect_callbacks(self)

        self.anv2_numsComboBox = self.anv2_builder.get_object('numsCmbBx', self.anv2_root)
        self.anv2_cats1ComboBox = self.anv2_builder.get_object('cats1CmbBx', self.anv2_root)
        self.anv2_cats2ComboBox = self.anv2_builder.get_object('cats2CmbBx', self.anv2_root)
        self.anv2_numsComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))
        self.anv2_cats1ComboBox['values'] = list(self.dataset.select_dtypes(include=['category', 'bool']))
        self.anv2_cats2ComboBox['values'] = list(self.dataset.select_dtypes(include=['category', 'bool']))

        self.anv2_root.grab_set()

    def anovaTwoOkBtnAction(self):
        selected_category1 = self.anv2_cats1ComboBox.get()
        selected_category2 = self.anv2_cats2ComboBox.get()
        selected_numeric = self.anv2_numsComboBox.get()
        if selected_category1:
            if selected_category2:
                if selected_numeric:
                    self.anv2_root.grab_release()
                    self.anv2_root.destroy()
                    result = fh.twoway_anova(selected_numeric, selected_category1, selected_category2, self.dataset)
                    self.console.configure(state='normal')
                    self.console.delete(1.0, "end")
                    self.console.insert("end", "Results of Two-Way ANOVA Test-----------------------------------------+\n\n")
                    self.console.insert("end", result)
                    self.console.insert("end", "\n\n+-----------------------------------------------------------------+\n")
                    self.console.configure(state='disable')
                else:
                    messagebox.showerror('Message', 'No DV was selected')
            else:
                messagebox.showerror('Message', 'Not enough IVs ware selected')
        else:
            messagebox.showerror('Message', 'Not enough IVs ware selected')
    # ------------------------------------------------------------------ #

    # Linear Regression functions -------------------------------------- #
    def regressionBtnAction(self):
        self.reg_root = tk.Tk()
        self.reg_root.title("Linear Regression")
        self.reg_root.resizable(False, False)
        self.reg_builder = pygubu.Builder() # Create a builder
        self.reg_builder.add_from_file('gui\\RegressionGUI.ui') # Load an ui file
        self.reg_mainwindow = self.reg_builder.get_object('regressionFrm', self.reg_root) # Create the widget using a master as parent
        self.reg_builder.connect_callbacks(self)

        self.reg_dvComboBox = self.reg_builder.get_object('numsCmbBx', self.reg_root)
        self.reg_iv1ComboBox = self.reg_builder.get_object('nums1CmbBx', self.reg_root)
        self.reg_iv2ComboBox = self.reg_builder.get_object('nums2CmbBx', self.reg_root)
        self.reg_dvComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))
        self.reg_iv1ComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))
        self.reg_iv2ComboBox['values'] = list(self.dataset.select_dtypes(include=['int', 'int64', 'float', 'float64']))

        self.reg_root.grab_set()

    def regressionOkBtnAction(self):
        selected_iv1 = self.reg_iv1ComboBox.get()
        selected_iv2 = self.reg_iv2ComboBox.get()
        selected_dv = self.reg_dvComboBox.get()
        if selected_iv1:
            if selected_iv2:
                if selected_dv:
                    self.reg_root.grab_release()
                    self.reg_root.destroy()
                    result = fh.liner_regression(selected_dv, selected_iv1, selected_iv2, self.dataset)
                    self.console.configure(state='normal')
                    self.console.delete(1.0, "end")
                    self.console.insert("end", "Results of linear Regression Test-------------------------------------+\n\n")
                    self.console.insert("end", result)
                    self.console.insert("end", "\n\n+-----------------------------------------------------------------+\n")
                    self.console.configure(state='disable')
                else:
                    messagebox.showerror('Message', 'No DV was selected')
            else:
                messagebox.showerror('Message', 'Not enough IVs ware selected')
        else:
            messagebox.showerror('Message', 'Not enough IVs ware selected')
    # ------------------------------------------------------------------ #

if __name__ == '__main__':
    root = tk.Tk()
    app = Facebook_Main()
    app.mainGUI(root)
    root.mainloop()