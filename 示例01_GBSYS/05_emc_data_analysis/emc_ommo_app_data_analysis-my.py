from os.path import expanduser
import h5py
import numpy as np
import matplotlib.pyplot as plt
import logging
import sys
import os.path
import math

logging.getLogger('emc_analysis')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


file_name = "C:\\workspace\\ommo_eval_sdk_v0.20.3\\ommo_app\data\\data0.hdf5"

# hdf5的指针
data_file = h5py.File(expanduser(file_name), 'r')
test_regions = np.array([[0,-1]])

# log文件的指针
txt_file_name = file_name[:file_name.rindex('\\')] + "\\" + 'console_log_'+file_name[file_name.rindex('\\')+1:-5]+'.txt'
#--print (txt_file_name)

if os.path.isfile(txt_file_name):
    open(txt_file_name, 'w').close()
file_handler = logging.FileHandler(txt_file_name)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message and not message.isspace():
            self.logger.log(self.level, message.strip())

    def flush(self):
        pass  # This method is needed for compatibility with `sys.stdout`
sys.stdout = LoggerWriter(logger, logging.INFO)

pad_seconds = 5


def contiguous_regions(condition, min_len=0):
    """Finds contiguous True regions of the boolean array "condition". Returns
    a 2D array where the first column is the start index of the region and the
    second column is the end index."""

    # Find the indicies of changes in "condition"
    d = np.diff(condition)
    idx, = d.nonzero()

    # We need to start things after the change in "condition". Therefore,
    # we'll shift the index by 1 to the right.
    idx += 1

    if condition[0]:
        # If the start of condition is True prepend a 0
        idx = np.r_[0, idx]

    if condition[-1]:
        # If the end of condition is True, append the length of the array
        idx = np.r_[idx, condition.size] # Edit

    # Reshape the result into two columns
    idx.shape = (-1,2)
    idx = idx[np.subtract(idx[:, 1], idx[:, 0]) > min_len]
    return idx


def rolling_bidirection_diff(x, x_max = 0, axis=0):
    if axis != 0:
        raise NotImplementedError('')
    else:
        # escalate int typing to handle overflows
        type = np.int64 if np.issubdtype(x.dtype, np.integer) else np.double
        x_ax = np.array(x, dtype=type)

    diff = x_ax[1:] - x_ax[:-1]
    under = diff < (-x_max/2)
    over = diff > x_max/2
    return diff + under * x_max - over * x_max


def moving_average_3d(data, window_size):
    # Ensure the input is a 2D NumPy array with 3 columns for 3D coordinates
    data = np.array(data, dtype=float)

    # Apply the moving average separately for each dimension (x, y, z)
    x_smooth = np.convolve(data[:, 0, 0], np.ones(window_size) / window_size, mode='valid')
    y_smooth = np.convolve(data[:, 0, 1], np.ones(window_size) / window_size, mode='valid')
    z_smooth = np.convolve(data[:, 0, 2], np.ones(window_size) / window_size, mode='valid')

    # Stack the smoothed x, y, z back into a 2D array again
    smoothed_data = np.stack((x_smooth, y_smooth, z_smooth), axis=-1)

    return smoothed_data


def downsample_average(data, chunk_size=1000):
    # Ensure the input is a 2D NumPy array with 3 columns for 3D coordinates
    data = np.array(data, dtype=float)

    # Calculate the number of complete chunks
    num_chunks = len(data) // chunk_size

    # Reshape each dimension separately, apply averaging for complete chunks
    x_avg = np.mean(data[:num_chunks * chunk_size, 0].reshape(-1, chunk_size), axis=1)
    y_avg = np.mean(data[:num_chunks * chunk_size, 1].reshape(-1, chunk_size), axis=1)
    z_avg = np.mean(data[:num_chunks * chunk_size, 2].reshape(-1, chunk_size), axis=1)

    # Handle any remaining points (the last incomplete chunk)
    if len(data) % chunk_size != 0:
        remainder_mean = np.mean(data[num_chunks * chunk_size:], axis=0)
        x_avg = np.append(x_avg, remainder_mean[0])
        y_avg = np.append(y_avg, remainder_mean[1])
        z_avg = np.append(z_avg, remainder_mean[2])

    # Stack the averaged x, y, z back into a 2D array
    downsampled_data = np.stack((x_avg, y_avg, z_avg), axis=-1)

    return downsampled_data


def process_device(device, t0, time_segments:np.ndarray):
    logging.info(f' device:{device.name}')

    timestamp_full = device['Timestamp']


    timestamp_delta = rolling_bidirection_diff(timestamp_full, 4294967296)
    time_passed = np.insert(timestamp_delta, 0, (timestamp_full[0, 0] - t0))
    # same length of original timestamp, starting from t0 across all devices
    time_passed = np.cumsum(time_passed)
    print('start time={} end time={} samples={}'.format(time_passed[0] / 16000000.0, time_passed[-1] / 16000000.0,
          np.shape(timestamp_full)[0]))
    for row in range(np.shape(time_segments)[0]):
        start_clock = max((time_segments[row,0] - pad_seconds) * 16000000.0, 0)
        end_clock = time_passed[-1]
        if time_segments[row, 1] > 0 and time_segments[row, 1] > time_segments[row, 0]:
            end_clock = min((time_segments[row,1] + pad_seconds) * 16000000.0, time_passed[-1])
        start_idx = np.where(time_passed >= start_clock)[0][0]
        end_idx = np.where(time_passed >= end_clock)[0][0] + 1
        delta_start_idx = max(start_idx - 1, 0)
        delta_end_idx = end_idx - 1

        timestamp = time_passed[start_idx:end_idx,...]#[20000:]
        encoder = device['Theta'][start_idx:end_idx,...]#[20000:]
        indicator = device['Indicator'][start_idx:end_idx,...]#[20000:]
        position = device['Position'][start_idx:end_idx,...]#[20000:]
        mag = device['Mag'][start_idx:end_idx,...]#[20000:]
        print(np.shape(timestamp), np.shape(encoder), np.shape(position))

        # smooth position and splice it into chunks of 1000
        smoothed_position = moving_average_3d(position, 20)
        downsampled_position = downsample_average(smoothed_position, 5000)
        position_delta_vector = downsampled_position[-1]-downsampled_position[0]
        position_delta_magnitude = np.linalg.norm(downsampled_position[0]-downsampled_position[-1])
        print("position delta vector = " + str(position_delta_vector), "position delta magnitude = " + str(position_delta_magnitude))

        # check timestamp
        delta = timestamp_delta[delta_start_idx:delta_end_idx,...]
        delta_values, delta_counts = np.unique(delta, return_counts=True)
        ts_events = np.logical_or(delta < 15980, delta > 10 * 15980)
        ts_event_idx = np.where(ts_events)[0]
        # don't add 1 to index, this gives us the timestamp at the beginning of the event
        # (next sample generates the event)
        try:
            ts_events_s = timestamp[ts_event_idx] / 16000000.0
            logging.info(f'Timestamp events:{ts_events_s}')
            logging.info(f'Timestamp events packets loss:{delta[ts_event_idx].flatten()/15984}')
        except Exception as e: print(e)

        fig, ax = plt.subplots(6, 1, figsize = (10, 8))
        fig.tight_layout(pad=3)
        fig.suptitle('device={} time={}'.format(device.name, time_segments[row]))
        ax[0].plot(delta, '.')
        ax[0].title.set_text("Timestamp Deltas"); ax[0].set_xlabel("Samples"); ax[0].set_ylabel("Delta Between Timestamps")
        logging.info(f' Timestamp deltas:{delta_values}\n counts:{delta_counts}')

        delta = rolling_bidirection_diff(encoder, 3600)
        delta_values, delta_counts = np.unique(delta, return_counts=True)
        encoder_events = np.logical_or(delta < 0, delta > 800)
        encoder_events_idx = np.where(encoder_events)[0]
        # don't add 1 to index, this gives us the timestamp at the beginning of the event
        # (next sample generates the event)
        encoder_events_s = timestamp[encoder_events_idx] / 16000000.0
        logging.info(f'Encoder events:{encoder_events_s}')

        ax[1].plot(delta, '.')
        ax[1].title.set_text("Encoder Deltas"); ax[1].set_xlabel("Samples"); ax[1].set_ylabel("Delta Between Encoder Measurments")
        logging.info(f' Encoder deltas:{delta_values}\n counts:{delta_counts}')

        position_centered = position[:, 0, :] - position[0, 0, :]
        downsampled_position_centered = downsampled_position - position[0, 0, :]

        ax[2].plot(position_centered, '.')
        ax[2].plot(np.linspace(0, len(position_centered) - 1, len(downsampled_position_centered)), downsampled_position_centered, linewidth=4)
        ax[2].title.set_text("Position Change"); ax[2].set_xlabel("Samples"); ax[2].set_ylabel("Position from origin (mm)"); ax[2].legend(['x', 'y', 'z', 'x filtered', 'y filtered', 'z filtered'], loc='right')
        ax[3].plot(position[:, 0, :], '.')
        ax[3].title.set_text("Absolute Position"); ax[3].set_xlabel("Samples"); ax[3].set_ylabel("Position from Base Station (mm)")
        ax[4].plot(indicator[:, 0, :], '.')
        ax[4].title.set_text("Indicator"); ax[4].set_xlabel("Samples"); ax[4].set_ylabel("Indicator value")
        if len(mag[:, 0, :]) > 500:
            ax[5].plot(range(math.floor(len(mag[:, 0, :])/2)-250,math.floor(len(mag[:, 0, :])/2)+250),mag[:, 0, :][math.floor(len(mag[:, 0, :])/2)-250:math.floor(len(mag[:, 0, :])/2)+250], '.')
            ax[5].title.set_text("Mag"); ax[5].set_xlabel("Samples"); ax[5].set_ylabel("Mag value")

        # position_diff_abs = np.abs(position_centered[1:] - position_centered[:-1])
        regions = contiguous_regions(np.any(np.abs(position_centered)>1, axis=1), 5)
        print("start_position={}".format(position[0,0,:]))
        logging.info(f' position over 2mm:{regions}')
        num_regions = np.shape(regions)[0]
        fig.savefig(file_name[:file_name.rindex('\\')] + "\\" + 'output_' + device.name[1:] +'_'+file_name[file_name.rindex('\\')+1:-5]+ '.png')
        if num_regions > 0:
            fig, ax = plt.subplots(num_regions + 1, 1, figsize = (10, 8))
            fig.tight_layout(pad=3)
            fig.suptitle('device={} time={} regions'.format(device.name, time_segments[row]))
            mask = np.ones(np.shape(position_centered)[0], dtype=bool)
            for i in range(num_regions):
                region_end_idx = regions[i,1]
                if region_end_idx >= np.shape(position_centered)[0]:
                    region_end_idx = np.shape(position_centered)[0]-1
                logging.info(f'Region start={timestamp[regions[i,0]] / 16000000.0} end={timestamp[region_end_idx] / 16000000.0}')
                mask[regions[i,0]:regions[i,1]] = False
                ax[i].plot(position_centered[regions[i,0]:regions[i,1]],'.')
                ax[i].title.set_text("Region of Deviation >2mm "+str(i)); ax[i].set_xlabel("Samples"); ax[i].set_ylabel("Deviation (mm)")
            ax[num_regions].plot(position_centered[mask],'.')
            ax[num_regions].title.set_text("Dataset with >2mm Deviations Removed"); ax[num_regions].set_xlabel("Samples"); ax[num_regions].set_ylabel("Deviation (mm)")
            fig.savefig(file_name[:file_name.rindex('\\')] + "\\" + 'deviations_' + device.name[1:] +'_'+file_name[file_name.rindex('\\')+1:-5]+ '.png')
        plt.show()


def process_file(file:h5py.File, test_regions):
    logging.info(f'file={file.filename}')
    logging.info(f'devices={file.keys()}')

    t0_all = []
    for device in file.values():
        t0_all.append(device['Timestamp'][0,0])

    t0_all = np.array(t0_all, dtype=np.int64)
    t0 = np.min(t0_all)
    t0_idx = np.where(t0_all==t0)[0]
    logging.info(f' t0_all={t0_all} t0={t0} t0_device_idx={t0_idx}')

    for device in file.values():
        if "Position" in device:
            process_device(device, t0, test_regions)

def main():
    process_file(data_file, test_regions)
    sys.stdout.flush()

if __name__ == "__main__":
    main()