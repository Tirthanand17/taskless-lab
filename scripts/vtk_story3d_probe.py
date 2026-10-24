"""Offline true-3D scene probe. No YouTube, external API or cloud bill.

Requires vtk, numpy, opencv-python in an approved renderer environment.
Example: python scripts/vtk_story3d_probe.py --output /existing/path/probe.mp4
Not a production-quality human avatar; do not use as a finished episode.
"""
from __future__ import annotations
import argparse
import math
from pathlib import Path
import cv2
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy

W, H, FPS, SECONDS = 854, 480, 18, 6


def scene_actor(renderer, source, name, color, opacity=1):
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(source.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.SetObjectName(name)
    actor.GetProperty().SetColor(*color)
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty().SetSpecular(.45)
    actor.GetProperty().SetSpecularPower(25)
    renderer.AddActor(actor)
    return actor


def block(renderer, name, center, dimensions, color, opacity=1):
    source = vtk.vtkCubeSource()
    source.SetCenter(*center)
    source.SetXLength(dimensions[0])
    source.SetYLength(dimensions[1])
    source.SetZLength(dimensions[2])
    return scene_actor(renderer, source, name, color, opacity)


def orb(renderer, name, xyz, radius, color):
    source = vtk.vtkSphereSource()
    source.SetCenter(*xyz)
    source.SetRadius(radius)
    source.SetPhiResolution(20)
    source.SetThetaResolution(24)
    return scene_actor(renderer, source, name, color)


def person(renderer, x, shirt, name):
    skin = (.78,.54,.37)
    hair = (.05,.047,.064)
    block(renderer, name+" torso", (x,1.52,.38), (.64,.9,.41), shirt)
    orb(renderer,name+" head",(x,2.27,.35),.30,skin)
    orb(renderer,name+" hair",(x,2.49,.43),.25,hair)
    for side in (-1, 1):
        orb(renderer,name+" hand",(x+side*.48,1.56,.21),.12,skin)
        orb(renderer,name+" eye",(x+side*.105,2.31,.072),.028,hair)
        block(renderer,name+" leg",(x+side*.17,.70,.4),(.23, .85, .28),(.09,.15,.24))


def render(output: Path):
    if output.suffix.lower() != ".mp4" or not output.parent.is_dir():
        raise ValueError("Pass --output as an MP4 inside an existing directory")
    r=vtk.vtkRenderer()
    r.SetBackground(.018,.042,.071)
    win=vtk.vtkRenderWindow()
    win.SetOffScreenRendering(True)
    win.SetSize(W,H)
    win.SetMultiSamples(0)
    win.AddRenderer(r)
    camera=vtk.vtkCamera()
    r.SetActiveCamera(camera)
    camera.SetViewUp(0,1,0)
    camera.SetViewAngle(34)
    teal=(.12,.85,.89)
    navy=(.035,.10,.18)
    block(r,"floor",(0,-.03,0),(13,.1,9),(.07,.16,.24))
    block(r,"back-wall",(0,2.7,3.2),(13,5.4,.15),navy)
    for x in (-5.7,-3.6,-1.5,.6,2.7,4.8):
        block(r,"depth wall glass",(x,2.8,3.09),(1.73,4.35,.05),(.07,.22,.3))
        block(r,"neon wall line",(x-.85,2.8,3.02),(.03,4.25,.04),teal)
    block(r,"3d screen",(0,3.35,3.0),(5.8,2.5,.1),(.06,.27,.37),.72)
    model=orb(r,"floating science model",(0,3.43,2.63),.70,teal)
    for i in range(5):
        block(r,"chart",(2.04+i*.22,2.5+i*.13,2.90),(.13,.32+i*.09,.05),(.2,.63,.9))
    block(r,"tabletop",(0,.89,-1.15),(6.8,.14,1.7),(.075,.19,.29))
    for x in (-2.9,2.9):
        block(r,"desk support",(x,.42,-1.12),(.12,.87,.12),(.14,.34,.4))
    block(r,"physical laptop",(0,1.3,-1.03),(1.0,.64,.08),(.12,.35,.56))
    for i,(x,shirt,name) in enumerate(((-2.2,(.04,.35,.42),"Asha"),
                                        (0,(.09,.18,.30),"Kabir"),
                                        (2.2,(.08,.43,.33),"Riya"))):
        person(r,x,shirt,name)
    tool=block(r,"interactive demo tool",(0,1.20,-1.55),(.30,.28,.30),(.98,.68,.29))
    light=vtk.vtkLight()
    light.SetPosition(-3,7,-3)
    light.SetIntensity(1.7)
    r.AddLight(light)
    light2=vtk.vtkLight()
    light2.SetPosition(3,4,-4)
    light2.SetColor(.5,.8,1.)
    light2.SetIntensity(.6)
    r.AddLight(light2)
    capture=vtk.vtkWindowToImageFilter()
    capture.SetInput(win)
    capture.SetInputBufferTypeToRGB()
    capture.ReadFrontBufferOff()
    writer=cv2.VideoWriter(str(output),cv2.VideoWriter_fourcc(*"mp4v"),FPS,(W,H))
    if not writer.isOpened():
        raise RuntimeError("MP4 writer not available")
    for f in range(FPS*SECONDS):
        t=f/FPS
        camera.SetPosition(-.4+.8*t/SECONDS,3.05-.12*t/SECONDS,-11.7+.65*t/SECONDS)
        camera.SetFocalPoint(0,1.7,.55)
        model.RotateY(1.2)
        tool.SetPosition(-.55+1.1*t/SECONDS,.18*math.sin(math.pi*t/SECONDS),0)
        tool.RotateY(3)
        win.Render()
        capture.Modified()
        capture.Update()
        data=vtk_to_numpy(capture.GetOutput().GetPointData().GetScalars())
        rgb=data.reshape(H,W,3)[::-1]
        image=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR).copy()
        cv2.rectangle(image,(0,H-94),(W,H),(5,18,31),-1)
        cv2.putText(image,"FLOWMINUTE LAB - TRUE 3D TECHNICAL PROBE",(25,27),
                    cv2.FONT_HERSHEY_SIMPLEX,.52,(236,246,250),1,cv2.LINE_AA)
        caption=("1. ASK A CLEAR QUESTION" if t < 2 else
                 "2. WATCH THE TOOL WORK" if t < 4 else
                 "3. CHECK THE RESULT")
        cv2.putText(image,caption,(31,H-41),
                    cv2.FONT_HERSHEY_SIMPLEX,.71,(232,250,250),2,cv2.LINE_AA)
        writer.write(image)
    writer.release()
    print("TRUE_3D_PROBE_CREATED",output,"NOT_A_RELEASE")


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--output",type=Path,required=True)
    args=cli.parse_args()
    render(args.output)
