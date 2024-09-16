import streamlit as st
from azure.storage.blob import BlobServiceClient
import json
import pandas as pd

# Azure Blob Storage接続情報
connection_string = st.secrets["connection_string"]
container_name = "node"
blob_name = "node.json"

# BlobServiceClientの作成
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)
blob_client = container_client.get_blob_client(blob_name)

class Node:
    def __init__(self, nodeId, nodeName, floorNumber, towerName, x, y, z):
        self.nodeId = nodeId
        self.nodeName = nodeName
        self.floorNumber = floorNumber
        self.towerName = towerName
        self.x = x
        self.y = y
        self.z = z

def get_nodes():
    try:
        blob_data = blob_client.download_blob().readall()
        nodes_data = json.loads(blob_data)
        nodes = [Node(node['nodeId'], node['nodeName'], node['floorNumber'], node['towerName'], node['x'], node['y'], node['z']) for node in nodes_data['nodes']]
    except Exception as e:
        nodes = []
        st.error(f"Error reading from blob: {e}")
    return nodes

def update_node(num, new_name, new_floor, new_tower):
    nodes = get_nodes()
    for node in nodes:
        if node.nodeId == num:
            node.nodeName = new_name
            node.floorNumber = new_floor
            node.towerName = new_tower
            break
    
    # nodes_data を再構築
    nodes_data = {"nodes": [], "edges": []}  # edges も保持
    for node in nodes:
        nodes_data["nodes"].append({
            "nodeId": node.nodeId,
            "nodeName": node.nodeName,
            "floorNumber": node.floorNumber,
            "towerName": node.towerName,
            "x": node.x,
            "y": node.y,
            "z": node.z
        })
    # edges を元のデータからコピー
    nodes_data["edges"] = json.loads(blob_client.download_blob().readall())["edges"]

    nodes_json = json.dumps(nodes_data)
    blob_client.upload_blob(nodes_json, overwrite=True)

def set_page_config():
    st.set_page_config(
        page_title="Node Editor",
        page_icon="📌",
        layout="wide"
    )

def get_unique_tower_names(nodes):
    return sorted(list(set(node.towerName for node in nodes if node.towerName)))

def edit_node_ui():
    st.header("_Edit_",divider="blue")
    
    nodes = get_nodes()
    node_dict = {node.nodeId: node.nodeName for node in nodes}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Select Node")
        selected_num = st.selectbox("Choose a Node", list(node_dict.keys()), format_func=lambda x: f"Node{x}")

    if selected_num is not None:
        node = next((n for n in nodes if n.nodeId == selected_num), None)
        if node:
            with col2:
                st.subheader("Edit Node Details")
                #部屋の名前の編集
                new_name = st.text_input("Name ", node.nodeName)
                
                #棟の編集
                unique_tower_names = get_unique_tower_names(nodes)
                unique_tower_names.append("Create New")  # "Create New" オプションを追加
                tower_selection = st.selectbox(
                    "Select Tower Name or Create New",
                    unique_tower_names,
                    index=unique_tower_names.index(node.towerName) if node.towerName in unique_tower_names else len(unique_tower_names) - 1
                )
                if tower_selection == "Create New":
                    new_tower = st.text_input("Enter New Tower Name", "")
                else:
                    new_tower = tower_selection
                
                #階の編集
                new_floor = st.number_input("Floor Number", value=node.floorNumber, min_value=0)
                

            if st.button("Update Node"):
                update_node(selected_num, new_name, new_floor, new_tower)
                st.success(f"Node {selected_num} updated successfully.")
        else:
            st.error("Node not found.")
    else:
        st.info("Please select a node to edit.")


def view_nodes_ui():
    st.header("_View_", divider="blue")
    nodes = get_nodes()

    tower_names = get_unique_tower_names(nodes)
    selected_tower = st.selectbox("Select Tower Name", ["All"] + tower_names)

    filtered_nodes = [node for node in nodes if node.nodeName] 

    if selected_tower != "All":
        filtered_nodes = [node for node in filtered_nodes if node.towerName == selected_tower]

    # NodeName でソート (A-Z)
    filtered_nodes = sorted(filtered_nodes, key=lambda x: x.nodeName)

    if not filtered_nodes:
        st.error("No nodes found with non-empty names.")
        return

    df = pd.DataFrame([
        {
            "Node ID": node.nodeId,
            "Node Name": node.nodeName,
            "Tower Name": node.towerName,
            "Floor Number": node.floorNumber
        } for node in filtered_nodes
    ])

    st.dataframe(df, use_container_width=True)

def main():
    set_page_config()
    
    st.title('Node Editor')
    
    col1, col2 = st.columns(2)
    with col1:
        edit_node_ui()
    with col2:
        view_nodes_ui()

if __name__ == "__main__":
    main()