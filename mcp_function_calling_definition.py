from mcp.server.fastmcp import FastMCP
import traceback
import sys
import inspect

server = FastMCP("Local Agent Helper")

# sheets: load_protocol_from_library
@server.tool()
def load_protocol_from_library(library_name: str=None, protocol_name: str=None) -> str:
    """
    Load a specified MRI protocol.
    Parameters:
        library_name (str): The name of the protocol library. Valid values are 'ge', 'site', and 'service'.
        protocol_name (str): The name or identifier of the protocol to load (e.g., 'Brain Routine').
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: select_task_by_index, select_series_by_index
@server.tool()
def select_task_or_series(index: str=None) -> str:
    """
    Select a task or series by index. If no index is specified, select the default task or series.
    Parameters:
        index (str): The index of the task to be selected as the current task. Default is None.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: duplicate_task_by_index, duplicate_series_by_index
@server.tool()
def duplicate_task_or_series(index: str=None) -> str:
    """
    Duplicate a task or series by index. If no index is specified, duplicate the default task or series.
    Parameters:
        index (str): The index of task or series to be duplicated. Default is None.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: start_examination
@server.tool()
def start_examination() -> str:
    """
    Start a new MRI exam or examination session.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: end_examination
@server.tool()
def end_examination() -> str:
    """
    End the current MRI exam session.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: set_parameter_by_index
@server.tool()
def set_parameter(index: str=None, param_name: str=None, param_value: str=None) -> str:
    """
    Set a specific parameter for a task or series identified by its index. If no index is specified, set the default one's parameter.
    Parameters:
        index (str): The index of the task or series in the task or series list. Default is None.
        param_name (str): The name of the parameter to set. Default is None.
        param_value (str): The value to assign to the parameter. Default is None.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

#sheets: save_task_by_index
@server.tool()
def save_task_or_series(index=None) -> str:
    """
    Save the RX(prescription) of a specific task or series identified by its index. If no index is specified, save the default one.
    Parameters:
        index : The index of the task in the task list to be confirmed. Default is None.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: prescan
@server.tool()
def prescan(method="automatic") -> str:
    """
    Perform prescan.
    Parameters:
        method (str): The method of prescan. Default is 'automatic'.:
            - "automatic": Perform an automatic prescan. Automatic prescan is commonly abbreviated as “auto prescan.
            - "manual": Perform a manual prescan.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: stop_prescan
@server.tool()
def stop_prescan() -> str:
    """
    Stop current prescan.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: start_scan
@server.tool()
def start_scan(index: str = None) -> str:
    """
    Execute the scan operation for a specific task or series identified by its index. If no index is specified, scan the default one.
    Parameters:
        index (str): The index of the task in the task list to be scanned. Default is None.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: pause_scan
@server.tool()
def pause_scan() -> str:
    """
    Pause the scanning operation.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: stop_scan
@server.tool()
def stop_scan() -> str:
    """
    Stop the scanning operation.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: resume_scan
@server.tool()
def resume_scan() -> str:
    """
    Resume the early stopped scanning.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: control_fan
@server.tool()
def control_fan(level: str=None) -> str:
    """
    Control fan and set speed level(optional).
    Parameters:
        level (str): The desired fan control level. Accepted values are:
            - "on": Turn on the fan
            - "low": Set fan to low speed
            - "medium": Set fan to medium speed
            - "high": Set fan to high speed
            - "off": Turn off the fan
            - None: Do nothing
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: control_fan
@server.tool()
def control_light(level: str=None) -> str:
    """
    Control light status and set brightness level(optional).
    Parameters:
        level (str): The desired light control level. Accepted values are:
            - "on": Turn on the light
            - "low": Set light to low brightness
            - "medium": Set light to medium brightness
            - "high": Set light to high brightness
            - "off": Turn off the light
            - None: Do nothing
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: set_hardware_landmark
@server.tool()
def set_hardware_landmark(value: float=None) -> str:
    """
    Sets the hardware landmark position.
    Parameters:
        value (float): The desired landmark position in millimeters (mm). Default is None, meaning do nothing.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: move_out
@server.tool()
def move_out_to_home_position() -> str:
    """
    Moves the MRI table/cradle to the HOME position.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: move_to_scan_position
@server.tool()
def move_in_to_scan_position() -> str:
    """
    Moves the MRI table/cradle in to the scan position.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: load_patient
@server.tool()
def load_patient(index: str=None, patient_id: str=None, record_type: str="all") -> str:
    """
    Loads a patient item from the MRI work list.
    Parameters:
        index (str): The record order on the work list UI. Default is None.
        patient_id (str): Optional patient ID to filter the record.
        record_type (str): The type of record to retrieve. Accepted values:
            - "local": Only local records
            - "ris": Only RIS records
            - "all": Both LOCAL and RIS records (default)
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: create_patient
@server.tool()
def create_patient(patient_id: str=None, weight: str=None) -> str:
    """
    Creates a patient record.
    Parameters:
        patient_id (str): The unique patient identifier.
        weight (str): The patient's weight in kilograms.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

def main():
    print("READY", file=sys.stderr, flush=True)  # Use stderr for debug messages
    try:
        server.run(transport="stdio")
    except Exception as e:
        print(f"[FATAL] Server crashed: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print("Starting server", file=sys.stderr, flush=True)  # Use stderr for debug messages
    main()