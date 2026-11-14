#!/usr/bin/env python3
"""Replay AFLNet queue samples and summarize PostgreSQL backend outcomes."""
import json,pathlib,socket,struct,sys,time
def frames(data):
    pos=0
    while pos+5<=len(data):
        n=struct.unpack("!I",data[pos+1:pos+5])[0]
        if n<4 or pos+1+n>len(data):break
        yield chr(data[pos]),data[pos+5:pos+1+n];pos+=1+n
def main():
    root=pathlib.Path(sys.argv[1]); files=sorted(p for p in root.glob("**/queue/id:*") if p.is_file())
    res={"queue_files":len(files),"connected":0,"errors":0,"resets":0,"empty_responses":0,"response_bytes":0,"response_frames":0,"ready_for_query":0,"error_responses":0,"command_completions":0,"timeouts":0,"samples":[]}
    for p in files:
        received=bytearray()
        try:
            with socket.create_connection(("127.0.0.1",8812),timeout=3) as s:
                res["connected"]+=1;s.settimeout(.25);s.sendall(p.read_bytes());deadline=time.monotonic()+1.25
                while time.monotonic()<deadline:
                    try:
                        b=s.recv(65536)
                        if not b:break
                        received.extend(b)
                    except socket.timeout:res["timeouts"]+=1;break
        except ConnectionResetError:res["resets"]+=1
        except (OSError,TimeoutError):res["errors"]+=1
        fs=list(frames(received));codes=[x[0] for x in fs];res["response_bytes"]+=len(received);res["response_frames"]+=len(fs)
        res["ready_for_query"]+=codes.count("Z");res["error_responses"]+=codes.count("E");res["command_completions"]+=codes.count("C")
        if not received:res["empty_responses"]+=1
        res["samples"].append({"file":p.name,"bytes_received":len(received),"backend_frames":len(fs),"ready_for_query":codes.count("Z"),"error_responses":codes.count("E")})
    (root/"queue-replay.json").write_text(json.dumps(res,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in res.items() if k!="samples"},indent=2))
if __name__=="__main__":main()
