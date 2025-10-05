import pandas as pd
import re
from typing import List, Dict, Any
from pathlib import Path

def parse_network_logs(log_lines: List[str]) -> pd.DataFrame:
    """
    Parse network logs and extract relevant information into a pandas DataFrame.
    
    Args:
        log_lines: List of log line strings
        
    Returns:
        pandas.DataFrame with parsed log data
    """
    
    parsed_data = []
    
    # Regex pattern to parse the log structure
    # Pattern breakdown:
    # - (\d+\.\d+): timestamp
    # - \[(\w+)\]: log level
    # - \((\w+)\): component (Batman)
    # - ([\w\.\[\]]+): host info like TestNetwork.txhost[0].app[0]
    # - for \(([^)]+)\): packet type
    # - bidirectional: orig = ([\d\.]+) neigh = ([\d\.]+): origin and neighbor IPs
    # - own_bcast = (\d+): own broadcast value
    # - real recv = (\d+): real received value
    # - local tq: (\d+): local transmission quality
    # - asym_penalty: (\d+): asymmetry penalty
    # - total tq: (\d+): total transmission quality
    
    log_pattern = re.compile(
        r'(\d+\.\d+)\[(\w+)\]\s*\(([^)]+)\)([^\s]+)\s+for\s+\(([^)]+)\):\s*'
        r'bidirectional:\s+orig\s*=\s*([\d\.]+)\s+neigh\s*=\s*([\d\.]+)\s*=>\s*'
        r'own_bcast\s*=\s*(\d+),\s*real\s+recv\s*=\s*(\d+),\s*local\s+tq:\s*(\d+),?\s*'
        r'asym_penalty:\s*(\d+),\s*total\s+tq:\s*(\d+)'
    )
    
    for line in log_lines:
        line = line.strip()
        if not line:
            continue
            
        match = log_pattern.match(line)
        if match:
            timestamp, log_level, component, host_info, packet_type, orig_ip, neigh_ip, own_bcast, real_recv, local_tq, asym_penalty, total_tq = match.groups()
            
            parsed_data.append({
                'timestamp': float(timestamp),
                'log_level': log_level,
                'component': component,
                'host': host_info,
                'packet_type': packet_type,
                'orig_ip': orig_ip,
                'neigh_ip': neigh_ip,
                'own_bcast': int(own_bcast),
                'real_recv': int(real_recv),
                'local_tq': int(local_tq),
                'asym_penalty': int(asym_penalty),
                'total_tq': int(total_tq)
            })
        else:
            #print(f"Warning: Could not parse line: {line}")
            continue
    # Create DataFrame
    df = pd.DataFrame(parsed_data)
    
    # Convert timestamp to datetime if needed (optional)
    # df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    
    return df

def parse_log_file(file_path: str) -> pd.DataFrame:
    """
    Parse a log file and return a pandas DataFrame.
    
    Args:
        file_path: Path to the log file
        
    Returns:
        pandas.DataFrame with parsed log data
    """
    try:
        with open(file_path, 'r', errors='ignore') as file:
            log_lines = file.readlines()
        return parse_network_logs(log_lines)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error reading file: {e}")
        return pd.DataFrame()

def process_all_logs_in_folder(folder_path: str = "results", recursive: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Process all General-*.out files in the specified folder and generate pickle files.
    Now supports recursive search and stores pickle files in the same directory as the original files.
    
    Args:
        folder_path: Path to the folder containing log files (default: "results")
        recursive: Whether to search recursively in subdirectories (default: True)
        
    Returns:
        Dictionary mapping relative file paths to processing results
    """
    import pickle
    
    # Create folder path object
    results_folder = Path(folder_path)
    
    if not results_folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        return {}
    
    # Dictionary to store processing results
    processing_results = {}
    
    # Pattern to match General-#*.out files (recursive or non-recursive)
    if recursive:
        log_files = list(results_folder.rglob("General-*.out"))
        print(f"Searching recursively in '{folder_path}' and all subdirectories...")
    else:
        log_files = list(results_folder.glob("General-*.out"))
        print(f"Searching in '{folder_path}' (non-recursive)...")
    
    if not log_files:
        print(f"No General-*.out files found in '{folder_path}'{' (recursive)' if recursive else ''}")
        return {}
    
    print(f"Found {len(log_files)} log files to process...")
    alldf=[]
    for log_file in sorted(log_files):
        try:
            # Get relative path from the base folder for better organization
            relative_path = log_file.relative_to(results_folder)
            
            # Extract file number from filename
            filename = log_file.name
            file_number = filename.replace("General-", "").replace(".out", "")
            
            print(f"Processing {relative_path}...")
            
            # Parse the log file
            df = parse_log_file(str(log_file))
            
            if df.empty:
                print(f"Warning: No data parsed from {relative_path}")
                processing_results[str(relative_path)] = {
                    'status': 'empty',
                    'records': 0,
                    'pickle_path': None
                }
                continue
            
            # Generate pickle file in the same directory as the original file
            pickle_filename = f"General-{file_number}.pkl"
            pickle_path = log_file.parent / pickle_filename
            
            with open(pickle_path, 'wb') as pickle_file:
                pickle.dump(df, pickle_file)
            # Store processing results
            processing_results[str(relative_path)] = {
                'status': 'success',
                'records': len(df),
                'pickle_path': str(pickle_path.relative_to(results_folder))
            }
            
            print(f"  → Created {pickle_path.relative_to(results_folder)} with {len(df)} records")
            
        except Exception as e:
            print(f"Error processing {log_file.name}: {e}")
            processing_results[str(relative_path)] = {
                'status': 'error',
                'records': 0,
                'pickle_path': None,
                'error': str(e)
            }
            continue
    
    successful_files = sum(1 for result in processing_results.values() if result['status'] == 'success')
    print(f"\nProcessing complete! Successfully generated {successful_files} pickle files.")
    return processing_results

def load_pickle_file(file_path: str) -> pd.DataFrame:
    """
    Load a DataFrame from a pickle file.
    
    Args:
        file_path: Path to the pickle file
        
    Returns:
        pandas.DataFrame
    """
    import pickle
    
    try:
        with open(file_path, 'rb') as pickle_file:
            df = pickle.load(pickle_file)
        return df
    except Exception as e:
        print(f"Error loading pickle file {file_path}: {e}")
        return pd.DataFrame()

def get_summary_stats(folder_path: str = "results", recursive: bool = True) -> pd.DataFrame:
    """
    Generate summary statistics for all processed pickle files.
    Now supports recursive search.
    
    Args:
        folder_path: Path to the folder containing pickle files
        recursive: Whether to search recursively in subdirectories (default: True)
        
    Returns:
        DataFrame with summary statistics
    """
    results_folder = Path(folder_path)
    
    # Search for pickle files (recursive or non-recursive)
    if recursive:
        pickle_files = list(results_folder.rglob("General-*.pkl"))
    else:
        pickle_files = list(results_folder.glob("General-*.pkl"))
    
    summary_data = []
    
    for pickle_file in sorted(pickle_files):
        try:
            df = load_pickle_file(str(pickle_file))
            
            # Extract file number and relative path
            file_number = pickle_file.name.replace("General-", "").replace(".pkl", "")
            relative_path = pickle_file.relative_to(results_folder)
            
            summary_data.append({
                'file_number': file_number,
                'relative_path': str(relative_path),
                'directory': str(relative_path.parent),
                'total_records': len(df),
                'unique_hosts': df['host'].nunique() if 'host' in df.columns else 0,
                'time_span': df['timestamp'].max() - df['timestamp'].min() if not df.empty else 0,
                'avg_local_tq': df['local_tq'].mean() if 'local_tq' in df.columns else None,
                'avg_total_tq': df['total_tq'].mean() if 'total_tq' in df.columns else None
            })
            
        except Exception as e:
            print(f"Error processing {pickle_file.name}: {e}")
    
    return pd.DataFrame(summary_data)

def find_all_log_directories(folder_path: str = "results") -> List[str]:
    """
    Find all directories containing General-*.out files.
    
    Args:
        folder_path: Path to the folder to search
        
    Returns:
        List of directory paths containing log files
    """
    results_folder = Path(folder_path)
    log_files = list(results_folder.rglob("General-*.out"))
    
    # Get unique directories containing log files
    directories = list(set(str(log_file.parent.relative_to(results_folder)) for log_file in log_files))
    return sorted(directories)

# Example usage
if __name__ == "__main__":
    # Process all log files in the results folder (recursive by default)
    processing_results = process_all_logs_in_folder("results", recursive=True)
    
    # Show processing results
    if processing_results:
        print("\nProcessing Results Summary:")
        for file_path, result in processing_results.items():
            status = result['status']
            records = result['records']
            if status == 'success':
                print(f"  ✓ {file_path}: {records} records → {result['pickle_path']}")
            elif status == 'empty':
                print(f"  ⚠ {file_path}: No data found")
            else:
                print(f"  ✗ {file_path}: Error - {result.get('error', 'Unknown error')}")
        
        # Generate summary statistics
        summary = get_summary_stats("results", recursive=True)
        if not summary.empty:
            print("\nSummary Statistics:")
            print(summary.to_string(index=False))
        
        # Show directories containing log files
        print(f"\nDirectories with log files:")
        directories = find_all_log_directories("results")
        for directory in directories:
            print(f"  - {directory}")
    
    # To load a specific pickle file later:
    # df = load_pickle_file("results/subdirectory/General-0.pkl")