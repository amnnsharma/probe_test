#Libraries installed
import requests
import streamlit as st
#from streamlit_lottie import st_lottie
from PIL import Image
import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import math
#from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
import os
import glob


#Helper functions
#strem travel distance: STD
#mst: Maximum stem travel (LST also same)
def efficiency(lr,std,r,R):
    if r==None:
        r=0.02
    if R==None:
        R=0.05
    n=flow_efficiency(R,r,std)
    if n==100:
        with st.container():
            st.write("## Result:")
            st.write("- Flow efficiency of this GLV is 100% of theoretical efficiency")
            st.write("- Load rate is "+str(round(lr,2))+" psi/inch")
            st.write("- Stem travel is "+str(round(std,3))+" inch")
            st.write("---")
    else:
        with st.container():
            st.write("## Result:")
            st.write("- Flow efficiency is "+str(n)+"% of theoretical efficency")
            st.write("- Load rate is "+str(round(lr,2))+" psi/inch")
            st.write("- Stem travel is "+str(round(std,3))+" inch")
            st.write("---")


def check_api_manual(up_d,up_p,down_d,down_p):

    #up_d,up_p=duplicate_remove(up_d,up_p)
    #down_d,down_p=duplicate_remove(down_d,down_p)

    slope1=[]

    for i in range(len(up_d)-1):
        slope1.append((up_p[i+1]-up_p[i])/(up_d[i+1]-up_d[i]+0.0000001))

    accn1=[]
    for i in range(len(slope1)-1):
        accn1.append((slope1[i+1]-slope1[i])/slope1[i]*100)


    slope2=[]

    for i in range(len(down_d)-1):
        slope2.append((down_p[i+1]-down_p[i])/(down_d[i+1]-down_d[i]+0.0000001))

    accn2=[]
    for i in range(len(slope2)-1):
        accn2.append((slope2[i+1]-slope2[i])/slope2[i]*100)
        
    for i in range(len(accn1)):
        if accn1[i]>500:
            up_d=up_d[:i+1] #To compensate size reduction of list due to slope and acceleration calculations 
            up_p=up_p[:i+1]
            break

    for i in range(len(accn2)):
        if accn2[i]>500:
            down_d=down_d[:i+1]
            down_p=down_p[:i+1]
            break

    distance=up_d +down_d
    pressure=up_p+down_p


    model=LinearRegression()
    model.fit(np.array(distance).reshape(-1,1), np.array(pressure))
    ma=model.coef_[0]
    ba=model.intercept_

    mst=max(distance)
    minimum_tra=min(distance)
    
    #message="$$ All TESTS ARE PASSED $$"
    #st.write(mst)
    return ma,mst,ba,minimum_tra


def plt_plobe(df1,df2,*mc,slope=False):
    with st.container():
        plot,_=st.columns((2,1))
        st.write("---")
        # Create a new figure and axis
        with plot:
            fig, ax = plt.subplots()

            plt.xticks(fontsize=5)
            plt.yticks(fontsize=5)

            # Plot the data from df1
            ax.scatter(df1[df1.columns[0]], df1[df1.columns[1]], label='Upstream Movement', marker='+')
                        
            #plt.hold(True)
            # Plot the data from df2
            ax.scatter(df2[df2.columns[0]], df2[df2.columns[1]], label='Downstream Movement', marker='x')

            # Set axis labels and chart title
            ax.set_xlabel('Stem Travel (inch)')
            ax.set_ylabel('Pressure (PSI)')
            ax.set_title('Probe Test')

            # Add legend
            ax.legend()

            #plt.show()
            ax.grid(True)

            if slope==False:
                # Show the plot
                st.pyplot(fig=fig)

            if slope==True:
                load_rate=mc[0]
                intercept=mc[1]
                mst=mc[2]
                X=np.linspace(mc[4],mc[3],10)
                #st.write(mst)
                Y=[x*load_rate+intercept for x in X]
                ax.plot(X, Y, 'g--', label="Load Rate")

                X2=mst*np.ones(10)
                Y2=np.linspace(mc[6],mc[5],10)
                ax.plot(X2,Y2,"m", label="Maximum Stem Travel Line")
                ax.legend()
                st.pyplot(fig=fig)





def duplicate_remove(list1,list2):
    
    i=0
    while len(list1)>1:
        if list1[i+1]==list1[i]:
            list1.pop(i)
            list2.pop(i)
        else:
            break

    j=-1
    while len(list1)>1:
        if list1[j]==list1[j-1]:
            list1.pop(j)
            list2.pop(j)
        else:
            break

    return list1, list2


def shortest_distance(x,y,m,b):
    
    d=abs(m*x-y+b)/math.sqrt(m*m+1)

    return d



def slope_lst(lista,listb):

    list1,list2=duplicate_remove(lista,listb)

    #
    #print(list1)
    #print(list2)

    model=LinearRegression()

    for i in range(len(list1)):

        if i==0: 
            #Initial slopes
            ma=(list2[1]-list2[0])/(list1[1]-list1[0])
            mb=(list2[-1]-list2[-2])/(list1[-1]-list1[-2])

            #print(ma, mb)

            #Initial intercepts
            ba=list2[0]-ma*list1[0]
            bb=list2[-1]-mb*list1[-1]

            #X and y for linear regression
            X1=np.array(list1[0:2])
            y1=np.array(list2[0:2])

            X2=np.array(list1[-3:])
            y2=np.array(list2[-3:])

        if i>1 and i<len(list1)-1:
            da=shortest_distance(list1[len(list1)-i-1],list2[len(list1)-i-1],ma,ba)
            db=shortest_distance(list1[len(list1)-i-1],list2[len(list1)-i-1],mb,bb)
            #print("da:"+str(da),"db:"+str(db))
            #print(list1[i])

            if da<=db:
                X1=np.append(X1,list1[2:len(list1)-i])
                y1=np.append(y1,list2[2:len(list1)-i])
                #print(list1[len(list1)-i-1])
                #print("LineA:"+str(len(list1)-i-1))
                #print("da:"+str(da),"db:"+str(db))
                #print(list1,list2)
                #print(X1,y1)
                #st.write(X1)
                model.fit(X1.reshape(-1,1), y1)
                ma=model.coef_[0]
                ba=model.intercept_
                minimum_travel=min(X1)
                break

            else:
                X2=np.append(X2,list1[len(list1)-i-1])
                y2=np.append(y2, list2[len(list1)-i-1])
                #print(list1[len(list1)-i-1])
                #print("LineB:"+str(len(list1)-i-1))
                #print("da:"+str(da),"db:"+str(db))
                model.fit(X2.reshape(-1,1),y2)
                mb=model.coef_[0]
                bb=model.intercept_

    return ma, (bb-ba)/(ma-mb),ba, minimum_travel
            


def flow_efficiency(R,r,H):
    B=math.cos(math.atan((H+math.sqrt(R*R-r*r))/r))
    A=math.pi*(r/B-R)*(R*B+r)

    Ap=math.pi*r*r

    if A>=Ap:
        n=100
    else:
        n=(A/Ap)*100

    return n


st.set_page_config(page_title="Probe Test", page_icon=":microscope:", layout="wide")

# Use local CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style/style.css")

#Navigation Bar
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",  # required
        options=["Home", "Analysis", "Contact"],  # required
        icons=["house", "book", "envelope"],  # optional
        menu_icon="cast",  # optional
        default_index=0,  # optional
        styles={
                "container": {"padding": "0!important", "background-color": "#003666"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#bfbfbf",
                },
                "nav-link-selected": {"background-color": "black"},
            },
        
        )

if selected=="Home":
    st.write("# Unveiling the Efficiency Secrets: Probe Testing for Gas Lift Valves")


    with st.container():
        #st.write("# Probe Testing in Gas Lift Valves")
        
        st.write("Probe testing plays a crucial role in the oil and gas industry, specifically in the evaluation of gas lift valves used in oil wells.This diagnostic procedure involves the insertion of a specialized tool, known as a probe, into the gas lift valve to measure essential parameters.")
        #st.write("The primary objective of probe testing is to assess the performance and condition of gas lift valves, ensuring their efficient operation. By measuring factors such as valve opening and closing pressures, gas flow rates, and response times, operators can identify potential issues such as leakage, improper functioning, or blockages.")
        #st.write("Regular probe testing allows operators to monitor the gas lift system's performance and optimize it for maximum oil production. By promptly addressing valve-related issues, operators can maintain the optimal flow of gas, ensuring enhanced production from the oil well.")
        #st.write("Probe testing serves as a valuable diagnostic tool, providing insights into the functionality of gas lift valves and facilitating proactive maintenance and optimization efforts. With its ability to identify and resolve potential issues, probe testing contributes to the overall success and productivity of gas lift operations in the oil and gas industry.")

    img_lottie_animation = Image.open("images/probe.jpg")

    with st.container():
        st.write("---")
        image_column, text_column = st.columns((1, 2))
        with image_column:
            st.image(img_lottie_animation)

        with text_column:
            st.header("Purpose of Probe Test")
            #st.write("##")
            text="""
                The purpose of the probe test in gas lift valves is to assess the performance and efficiency of the valve system. 
                It serves as a diagnostic tool to evaluate the functionality of the valves and identify any potential issues or malfunctions. 
                By conducting the probe test, operators can gather valuable data on the valve's operation, including pressure differentials, flow rates, and gas lift efficiency. 
                This information helps in optimizing the gas lift process, enhancing production rates, and ensuring the effective lifting of fluids from the wellbore.
                """
            st.write(text)

            st.header("Procedure and Equipment")

            st.write("""
            The probe test involves a systematic procedure and the use of specialized equipment. 
            Firstly, pressure gauges and flow meters are installed at strategic locations along the gas lift system. 
            These instruments measure the pressure differentials and flow rates at various stages of the valve system. 
            A probe is then inserted into the gas lift valve to capture critical data such as valve opening and closing pressures, gas injection rates, and fluid flow characteristics. 
            The collected data is carefully recorded and analyzed to evaluate the valve's performance, identify any abnormalities, and make necessary adjustments to optimize the gas lift operation.""")

            st.write("[Learn More>](https://onepetro.org/SPELACP/proceedings-abstract/99LACPEC/All-99LACPEC/SPE-53969-MS/59863)")
        #with right_column:
        #    st_lottie(lottie_coding, height=300, key="coding")


if selected=="Analysis":
    
    def display_table(data):
        # Split the data into rows using the newline character ('\n')
        rows = data.split('\n')

        # Initialize an empty list to store the table rows
        table_data = []

        # Iterate over the rows
        for row in rows:
            # Split each row into columns using the tab character ('\t')
            columns = row.split('\t')

            # Append the columns to the table_data list
            table_data.append(columns)
        
        table_data.pop(-1)

        df=pd.DataFrame(table_data, columns=["Stem Travel (inch)","Pressure(PSI)"])

        #df = df.rename_axis('SN')
        df.index = range(1, len(df) + 1)
        
        
        # Display the table
        #st.table(df)

        return df

    with st.container():
        st.write("# Insights into Performance Evaluation")
        st.write("### Instructions:")
        st.write(" - Copy and paste the Upstream travel and Downstream travel table below")
        left,right=st.columns((1.4,2))
        with left:
            st.write("- You can get the sample probe test data from [here](https://docs.google.com/spreadsheets/d/1qGdsDLv2kQBTRcwLCHILnjHvfJu7ZL2i/edit?usp=sharing&ouid=114837832547667718557&rtpof=true&sd=true)")
        #with right:
        #    path = os.getcwd()
        #    csv_file = glob.glob(os.path.join(path, "*.xlsx"))
        #    df=pd.read_excel(csv_file)
        #    st.download_button(label="Download Excel",data=df)
    with st.container():
        st.write("---")
        left_table,_,right_table,blank = st.columns((1.7,0.8,1.7,2), gap="large")

        with left_table:
            st.subheader("Upstream Travel")
            #heading1,heading2=st.columns(2)
            #with heading1:
            #    st.write("###### Stem Travel (in)")
            #with heading2:
            #    st.write("###### Pressure(psi)")
            table1_data = st.text_area("Enter stem travel (in) & pressure(psi):", height=250)
            if st.text_input("Port size radius(in):")!="":
                r=float(st.text_input("Port size radius(in):"))
            else:
                r=""

        with right_table:
            st.subheader("Downstream Travel")
            table2_data = st.text_area("Enter stem travel (in)  & pressure(psi):", height=250)
            if st.text_input("Ball radius (in):")!="":
                R=float(st.text_input("Ball radius (in):"))
            else:
                R=""

        st.write("")


        _,btn,_,_ = st.columns((1.8,1.8,1.2,2), gap="large")
        disp=0
        # Button to display the entered data in table format
        with btn:
            if st.button("Evaluate"):
                disp=1
            
        if disp==1:
                
            table1,_,table2,_=st.columns((2,0.5,2.2,1),gap="large")
            # Check if both text areas are not empty
            if table1_data and table2_data: 
                # Display the tables based on the input data
                with table1:
                    st.write("#### Upstream movement table:")
                    df1=display_table(table1_data)
                    st.table(df1)
                    df1=df1.astype(float)

                with table2:
                    st.write("#### Downstream movement table:")
                    df2=display_table(table2_data)
                    st.table(df2)
                    df2=df2.astype(float).sort_values("Pressure(PSI)")

                st.write("---")


                #Plotting the original dataset
                _,plot1,_=st.columns((0.1,3,0.1))
                with plot1:
                    st.write("## Plotting the original data points:")
                    plt_plobe(df1,df2)

                #Plotting the modified dataset
                list_ust = df1[df1.columns[0]].values.tolist()
                list_upsi=df1[df1.columns[1]].values.tolist()

                #print(list_u[0])
                mu,lstu,bau,minimum_travel1=slope_lst(list_ust,list_upsi)

                list_dst = df2[df2.columns[0]].values.tolist()
                list_dpsi=df2[df2.columns[1]].values.tolist()
                md,lstd,bad,minimum_travel2=slope_lst(list_dst,list_dpsi)

                #Duplicate remove and plot
                list1,list2=duplicate_remove(list_ust,list_upsi)
                list3,list4=duplicate_remove(list_dst,list_dpsi)

                #st.write(list1[0])
                
                df1_new=pd.DataFrame({'ST': list1, 'PSI': list2})
                df2_new=pd.DataFrame({'ST': list3, 'PSI': list4})

                #print(df2_new)

                #Plot after removing duplicates

                _,plot2,_=st.columns((0.1,3,0.1))


                with plot2:
                    #st.write("---")
                    st.write("## After removing redundant points:")
                    plt_plobe(df1_new,df2_new)

                avg_slope=(mu+md)/2
                lstd=max(lstu,lstd)
                ba=(bau+bad)/2
                minimum_travel=min(minimum_travel1,minimum_travel2)

                #st.write(mu,md,avg_slope)
                #st.write(bau,bad,ba)

                _,plot3,_=st.columns((0.1,3,0.1))
                
                with plot3:
                    st.write("## Laod rate graph as per 19g2:")
                    plt_plobe(df1_new,df2_new,avg_slope, ba, lstd, min(list1[0],list3[0]),max(list1[-1],list3[-1]), min(list2[0],list4[0]),max(list2[-1],list4[-1]),slope=True)
                    efficiency(avg_slope,lstd,r if r!="" else None,R if R else None)

                _,plot4,_=st.columns((0.1,3,0.1))

                with plot4:
                    st.write("## Load rate graph as per 19v2:")
                    slope_v2,mstv2,interceptv2,minimum_travelv2=check_api_manual(list1,list2,list3,list4)
                    plt_plobe(df1_new,df2_new,slope_v2, interceptv2, mstv2, min(list1[0],list3[0]),max(list1[-1],list3[-1]), min(list2[0],list4[0]),max(list2[-1],list4[-1]),slope=True)
                    efficiency(slope_v2,mstv2,r if r!="" else None,R if R else None)


            else:
                with table1:
                    st.warning("Please enter data in both text areas.")

    
if selected=="Contact":
        
        # ---- CONTACT ----
    with st.container():
        st.write("---")
        st.header("Get In Touch With Us!")
        st.write("##")

        # Documention: https://formsubmit.co/ !!! CHANGE EMAIL ADDRESS !!!
        contact_form = """
        <form action="https://formsubmit.co/c0187a62200d807b7472b0e5695ba4e6" method="POST">
            <input type="hidden" name="_captcha" value="false">
            <input type="text" name="name" placeholder="Your name" required>
            <input type="email" name="email" placeholder="Your email" required>
            <textarea name="message" placeholder="Your message here" required></textarea>
            <button type="submit">Send</button>
        </form>
        """
        left_column, right_column = st.columns(2)
        with left_column:
            st.markdown(contact_form, unsafe_allow_html=True)
        with right_column:
            st.empty()
