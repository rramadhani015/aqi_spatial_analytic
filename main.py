import streamlit as st
import io
import pandas as pd
import snowflake.connector
import plotly.express as px
# import matplotlib.pyplot as plt

# def fetch_query_pd(query):
#     with conn.cursor() as cur:
#         cur.execute(query)
#         return cur.fetch_pandas_all()

# Define a function to manage session state for the DataFrame
def manage_session_state(data_df):
    if "data_df" not in st.session_state:
        st.session_state.data_df = data_df
    return st.session_state.data_df

def convert_to_pandas(file_obj):
  """
  Converts a CSV or XLS file uploaded by the user to a pandas DataFrame.

  Args:
    file_obj: A file object uploaded through Streamlit.

  Returns:
    A pandas DataFrame containing the data from the file.
  """
  # Check file extension
  if file_obj.name.endswith(".csv"):
    df = pd.read_csv(file_obj)
  elif file_obj.name.endswith(".xls") or file_obj.name.endswith(".xlsx"):
    df = pd.read_excel(file_obj)
  else:
    raise ValueError("Unsupported file format. Supported formats: CSV, XLS, XLSX")

  return df

def plot_chart(df, x_component, y_component, chart_type):
    """
    Creates an interactive chart using Plotly.

    Args:
      df: A pandas DataFrame.
      x_component: The column name for the x-axis.
      y_component: The column name for the y-axis.
      chart_type: The type of chart to generate (e.g., "bar", "line", "pie").
    """
    if chart_type == "bar":
        fig = px.bar(df, x=x_component, y=y_component, title="Bar Chart")
    elif chart_type == "line":
        fig = px.line(df, x=x_component, y=y_component, title="Line Chart")
    elif chart_type == "pie":
        fig = px.pie(df, values=y_component, names=x_component, title="Pie Chart")
    else:
        st.error(f"Invalid chart type: {chart_type}")
        return

    st.plotly_chart(fig)

def show_correlation_matrix(df, selected_columns=None):
    """
    Displays a correlation matrix for the DataFrame, optionally allowing the user to
    select which columns to include. Only numeric columns are used for correlation.

    Args:
      df: A pandas DataFrame.
      selected_columns: A list of column names to include in the correlation matrix.
                         If None, all numeric columns are used.
    """
    if selected_columns is None:
        # Filter numeric columns only
        selected_columns = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]

    if len(selected_columns) > 0:
        corr_df = df[selected_columns].corr()
        fig = px.imshow(corr_df, labels=dict(color="Correlation"), x=selected_columns, y=selected_columns, title="Correlation Matrix")
        st.plotly_chart(fig)
    else:
        st.warning("No numeric columns selected for the correlation matrix.")

def show_column_description(df):
    """
    Displays a description of each column in the DataFrame.

    Args:
      df: A pandas DataFrame.
    """
    st.subheader("Column Descriptions")
    column_data = []
    for col in df.columns:
        column_data.append({
            'Column Name': col,
            'Data Type': df[col].dtype,
            'Description': df[col].describe().to_dict()
        })
    st.write(pd.DataFrame(column_data))


def change_data_types(df):
    """
    Displays a form to change data types for specific columns in the DataFrame.

    Args:
      df: A pandas DataFrame.
    """
    st.subheader("Change Data Types")
    with st.form(key='data_type_form'):
        column_names = df.columns
        selected_column = st.selectbox("Select Column:", column_names)
        new_data_type = st.selectbox("Select New Data Type:", ['int64', 'float64', 'object', 'datetime64[ns]', 'timedelta'])
        submit_button = st.form_submit_button(label='Apply Changes')
        if submit_button:
            try:
                df[selected_column] = df[selected_column].astype(new_data_type)
                st.success(f"Data type for column '{selected_column}' changed to {new_data_type}.")
                # show_column_description(df)
            except Exception as e:
                st.error(f"Error: {e}")
    return df

def visualize():
  # Streamlit app
  st.title("CSV/XLS Visualization")

  uploaded_file = st.file_uploader("Upload a CSV or XLS file", type=["csv", "xls", "xlsx"])

  if uploaded_file is not None:
      try:
          data_df = convert_to_pandas(uploaded_file)
          manage_session_state(data_df)

          st.subheader("Data Preview")
          st.dataframe(data_df.head())
          st.write(f"Shape of the DataFrame: {data_df.shape}")

          modified_df = change_data_types(st.session_state.data_df)
          show_column_description(modified_df)
          show_correlation_matrix(modified_df)

          # chart_type = st.selectbox("Choose chart type:", ["bar", "line", "pie", "Correlation Matrix"])
          
          chart_type = st.selectbox("Choose chart type:", ["bar", "line", "pie"])

          if chart_type in ["bar", "line", "pie"]:
              x_component = st.selectbox("Select X Component:", modified_df.columns)
              y_component = st.selectbox("Select Y Component:", modified_df.columns)
              plot_chart(modified_df, x_component, y_component, chart_type)

      except ValueError as e:
          st.error(e)

# Function to display the login/logout button
def login_logout():

    if not hasattr(st.session_state, "logged_in") or not st.session_state.logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.logged_in = True
                st.success("Login successful!")
                # st.rerun()
            else:
                st.error("Login failed. Please try again.")
    else:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.success("Logout successful.")
            # st.rerun()

    # st.experimental_rerun()

# Function to display the home page
def display_home():
    st.header("Data Visualization")

def authenticate(username, password):
    # Replace this with your actual authentication logic
    return username == "admin" and password == "admin"

def gen_query():
    st.header("Generate Query")
    
def converter():
    st.header("Convert XLS to CSV")

def split_csv():
    st.header("Split CSV")
    
def rag_llm():
    st.header("RAG LLM")

# Main function to run the Streamlit app
def main():
    # Connect to PostgreSQL database
    # conn ="connect_to_postgres()"
    st.sidebar.title("Navigation")

    login_logout()
    
    if not hasattr(st.session_state, "logged_in") or not st.session_state.logged_in:
        st.warning("You need to log in first.")
    else:
        # Sidebar menu
        menu = ["Home", "Visualize","Convert","Split CSV","RAG LLM"]
        choice = st.sidebar.selectbox("Menu", menu)

        # Home
        if choice == "Home":
            display_home()

        # Input New Items
        elif choice == "Visualize":
            visualize()
            
        # Generate Query
        elif choice == "Generate Query":
            gen_query()

        # XLS to CSV
        elif choice == "Convert":
            converter()
            
        # divide 
        elif choice == "Split CSV":
            split_csv()
            
        # RAG LLM
        elif choice == "RAG LLM":
            rag_llm()


    # Close the PostgreSQL connection
    # conn.close()

# Run the Streamlit app
if __name__ == "__main__":
    
    main()
