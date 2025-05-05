from google.cloud.dialogflowcx_v3beta1.types import Flow

def remove_transition_routes(flows_client, agent_path):
    flows = flows_client.list_flows(parent=agent_path)
    for flow in flows:
        flow_obj = flows_client.get_flow(name=flow.name)
        
        # Special handling for Default Start Flow
        if "00000000-0000-0000-0000-000000000000" in flow.name:
            print("⚠️ Skipping transition route removal for Default Start Flow")
            continue
            
        original_routes = getattr(flow_obj, "transition_routes", [])
        filtered_routes = [route for route in original_routes if not route.intent]
        
        if len(filtered_routes) != len(original_routes):
            try:
                updated_flow = Flow(
                    name=flow.name,
                    transition_routes=filtered_routes
                )
                flows_client.update_flow(
                    flow=updated_flow,
                    update_mask={"paths": ["transition_routes"]}
                )
                print(f"🧹 Removed flow-level intent transition routes in: {flow.name}")
            except Exception as e:
                print(f"⚠️ Failed to update flow '{flow.name}': {e}")