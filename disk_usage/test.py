# from pathlib import Path 


# f = Path('../test')

# for i in f.rglob("*"):
#     # print(i.resolve())
#     if str(i.resolve()) in "/Users/prughani/git/ga_data_archive/test/d1":
#         print('skip',i)
#         continue
#     print(i)
 

from multiprocessing import Process, Queue
import time
import sys





def reader_proc(queue: Queue, h):
    """Read from the queue; this spawns as a separate Process"""
    print(h)
    while True:
        msg = queue.get()  # Read from the queue and do nothing
        if queue.qsize == 0:
            print('ENDED')
            break
        if msg == "DONE":
            break


def writer(count, num_of_reader_procs, queue):
    """Write integers into the queue.  A reader_proc() will read them from the queue"""
    for ii in range(0, count):
        if ii < 10:
            print(ii)
        queue.put(ii)  # Put 'count' numbers into queue

    ### Tell all readers to stop...
    for ii in range(0, num_of_reader_procs):
        print('Done')
        queue.put("DONE")


def start_reader_procs(qq, num_of_reader_procs, *arg):
    """Start the reader processes and return all in a list to the caller"""
    all_reader_procs = list()
    for ii in range(0, num_of_reader_procs):
        ### reader_p() reads from qq as a separate process...
        ###    you can spawn as many reader_p() as you like
        ###    however, there is usually a point of diminishing returns
        reader_p = Process(target=reader_proc, args=(qq, *arg))
        reader_p.daemon = True
        reader_p.start()  # Launch reader_p() as another proc
        print(type(reader_p))
        all_reader_procs.append(reader_p)

    return all_reader_procs


if __name__ == "__main__":
    num_of_reader_procs = 8
    qq = Queue()  # writer() writes to qq from _this_ process
    for count in [10**4, 10**5, 10**6][:1]:
        assert 0 < num_of_reader_procs <= 8
        all_reader_procs = start_reader_procs(qq, num_of_reader_procs, 'hello')

        # Queue stuff to all reader_p()
        writer(count, len(all_reader_procs), qq)
        print("All reader processes are pulling numbers from the queue...")

        _start = time.time()
        for idx, a_reader_proc in enumerate(all_reader_procs):
            print("    Waiting for reader_p.join() index %s" % idx)
            a_reader_proc.join()  # Wait for a_reader_proc() to finish

            print("        reader_p() idx:%s is done" % idx)

        print(
            "Sending {0} integers through Queue() took {1} seconds".format(
                count, (time.time() - _start)
            )
        )
        print("")
